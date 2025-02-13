import logging
import time
from functools import lru_cache

from arango.client import ArangoClient
from django.db import models
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from cegs_portal.search.models import DNAFeature
from cegs_portal.search.models import Experiment as Expr
from cegs_portal.search.models.validators import validate_accession_id
from cegs_portal.uploads.data_loading.analysis import Analysis
from cegs_portal.uploads.data_loading.experiment import Experiment
from cegs_portal.uploads.data_loading.metadata import (
    AnalysisMetadata,
    AnalysisMetadataKeys,
    ExperimentMetadata,
    ExperimentMetadataKeys,
)
from cegs_portal.uploads.view_models import get_next_experiment_accession

logger = logging.getLogger(__name__)

HOSTNAME = "https://db.catalog.igvf.org"
DB_NAME = "igvf"
HEADERS = {"Content-Type": "application/json"}
PAYLOAD = {"username": "guest", "password": "guestigvfcatalog"}


@lru_cache
def get_gene_name(ensembl_id, assembly):
    gene = DNAFeature.objects.filter(ensembl_id=ensembl_id, ref_genome=assembly).exclude(chrom_name="chrY")

    match len(gene):
        case 1:
            return gene.first().name
        case 0:
            logger.error(f"No Features {ensembl_id} on assembly {assembly}")
            raise DNAFeature.DoesNotExist()
        case _:
            logger.error(f"Multiple Features {ensembl_id} on assembly {assembly}")
            raise DNAFeature.MultipleObjectsReturned()


def gen_tested_elements(data):
    for chrom in data["sources"]:
        for reo in chrom["reos"]:
            reo = reo["reo"]
            reo_pval = reo["log10pvalue"]

            if reo_pval is None:
                continue

            yield {
                "chrom": reo["source_chr"],
                "start": reo["source_start"],
                "end": reo["source_end"],
                "strand": "",
                "parent_chrom": "",
                "parent_start": "",
                "parent_end": "",
                "parent_strand": "",
                "facets": "",
                "misc": "",
            }


def gen_reos(data):
    assembly = "hg38"
    for chrom in data["sources"]:
        for reo in chrom["reos"]:
            reo = reo["reo"]
            reo_pval = reo["log10pvalue"]

            if reo_pval is None:
                continue

            reo_sig = reo["significant"]
            reo_effect = reo["score"]
            gene_ensembl_id = reo["_to"].split("/")[1]
            gene_name = get_gene_name(gene_ensembl_id, assembly)

            yield {
                "chrom": reo["source_chr"],
                "start": reo["source_start"],
                "end": reo["source_end"],
                "strand": "",
                "gene_name": gene_name,
                "gene_ensembl_id": gene_ensembl_id,
                "raw_p_val": reo_pval,
                "adj_p_val": reo_sig,
                "effect_size": reo_effect,
                "facets": "",
            }


def load_experiment(data, experiment_accession_id):
    logger.info(f"{experiment_accession_id}: Loading experiment")
    metadata = ExperimentMetadata(
        {
            ExperimentMetadataKeys.NAME: "IGVF Analysis Results",
            ExperimentMetadataKeys.DESCRIPTION: "Analysis results from IGVF",
            ExperimentMetadataKeys.SOURCE_TYPE: "Genomic Element",
            ExperimentMetadataKeys.BIOSAMPLES: [{"cell_type": "unknown", "tissue_type": "unknown"}],
            ExperimentMetadataKeys.PROVENANCE: Expr.Provenance.IGVF,
            ExperimentMetadataKeys.TESTED_ELEMENTS_METADATA: {
                "filename": "",
                "file_location": "",
                "genome_assembly": "hg38",
                "url": "https://db.catalog.igvf.org/",
            },
        },
        experiment_accession_id,
    )
    Experiment(metadata).add_generator_data_source(gen_tested_elements(data)).load().save()

    logger.info(f"{experiment_accession_id}: Loading analysis")

    metadata = AnalysisMetadata(
        {
            AnalysisMetadataKeys.NAME: "IGVF Analysis Results",
            AnalysisMetadataKeys.DESCRIPTION: "Analysis results from IGVF",
            AnalysisMetadataKeys.GENOME_ASSEMBLY: "hg38",
            AnalysisMetadataKeys.P_VAL_THRESHOLD: "0.05",
            AnalysisMetadataKeys.SOURCE_TYPE: "Genomic Element",
            AnalysisMetadataKeys.RESULTS: {
                "filename": "",
                "file_location": "",
                "url": "https://db.catalog.igvf.org/",
            },
        },
        experiment_accession_id,
    )
    Analysis(metadata).add_generator_data_source(gen_reos(data)).load().save()

    logger.info(f"{experiment_accession_id}: Finished loading data")


@db_periodic_task(crontab(day="*/10"))
def update_coverage_data():
    client = ArangoClient(hosts=HOSTNAME)
    db = client.db(DB_NAME, username=PAYLOAD["username"], password=PAYLOAD["password"])
    async_db = db.begin_async_execution(return_result=True)

    query = async_db.aql.execute(
        """
        LET reos = (
            FOR rr IN genomic_elements
            FOR g in genes
            FOR rrg IN genomic_elements_genes
              FILTER rrg._to == g._id && rrg._from == rr._id && HAS(rrg, "significant")
              RETURN merge(rrg, { "gene_chr": g.chr, "gene_start": g.`start`, "gene_end": g.`end`, "source_chr": rr.chr, "source_start": rr.`start`, "source_end": rr.`end`  })
        )

        LET sources = (FOR reo IN reos
        COLLECT chr = reo.source_chr INTO groups
        RETURN { "chr": chr, "reos": groups})

        LET genes = (FOR reo IN reos
        COLLECT chr = reo.gene_chr INTO groups
        RETURN { "chr": chr, "reos": groups})

        RETURN {"sources": sources, "genes": genes}
    """
    )

    if query is None:
        return

    logger.debug("IGVF Query started")
    # Let's wait until the jobs are finished.
    while query.status() != "done":
        logger.debug("IGVF Query working")
        time.sleep(10)

    logger.debug(f"IGVF Query complete: {query.status()}")
    result = query.result().pop()

    experiment_accession_id = get_next_experiment_accession()

    cache = QueryCache(value=result, experiment_accession_id=experiment_accession_id)
    cache.save()

    load_experiment(result, experiment_accession_id)


# Create your models here.
class QueryCache(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    value = models.JSONField(null=True, blank=True)
    experiment_accession_id = models.CharField(max_length=17, validators=[validate_accession_id], null=True, blank=True)
