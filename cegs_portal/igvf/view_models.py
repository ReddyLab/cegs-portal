import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, StrEnum
from functools import lru_cache
from typing import Optional

from arango.client import ArangoClient
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from cegs_portal.igvf.models import QueryCache
from cegs_portal.search.models import DNAFeature, EffectObservationDirectionType
from cegs_portal.search.models import Experiment as Expr
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

LARGE_BUCKET_SIZE = 2_000_000
SMALL_BUCKET_SIZE = 100_000
CHROM_NAMES = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "X",
    "Y",
    "MT",
]

HOSTNAME = "https://db.catalog.igvf.org"
DB_NAME = "igvf"
HEADERS = {"Content-Type": "application/json"}
PAYLOAD = {"username": "guest", "password": "guestigvfcatalog"}


class GetIGVFException(Exception):
    pass


class CoverageType(Enum):
    COUNT = 0
    SIGNIFICANCE = 1
    EFFECT = 2


@dataclass
class FilterIntervals:
    effect: tuple[float, float]
    sig: tuple[float, float]


@dataclass
class Filter:
    categorical_facets: set[str]
    chrom: Optional[int]
    coverage_type: CoverageType
    numeric_intervals: Optional[FilterIntervals]


def get_filter(filters, chrom, coverage_type):
    if chrom is not None:
        chrom = CHROM_NAMES.index(chrom)

    if len(filters) > 1:
        effect_size_interval, sig_interval = filters[1]
        numeric_intervals = FilterIntervals(
            effect=(effect_size_interval[0], effect_size_interval[1]), sig=(sig_interval[0], sig_interval[1])
        )
    else:
        numeric_intervals = None

    match coverage_type:
        case "coverage-type-count":
            coverage_type = CoverageType.COUNT
        case "coverage-type-sig":
            coverage_type = CoverageType.SIGNIFICANCE
        case "coverage-type-effect":
            coverage_type = CoverageType.EFFECT
        case _:
            coverage_type = CoverageType.COUNT

    return Filter(
        categorical_facets=set(filters[0]),
        chrom=chrom,
        numeric_intervals=numeric_intervals,
        coverage_type=coverage_type,
    )


def view_facets(stats):
    return [
        {
            "id": "Direction",
            "name": "Direction",
            "facet_type": "FacetType.CATEGORICAL",
            "description": "Effect change direction",
            "coverage": ["Target", "Source"],
            "values": {
                "Depleted Only": "Depleted Only",
                "Enriched Only": "Enriched Only",
                "Non-significant": "Non-significant",
            },
        },
        {
            "id": "Effect Size",
            "name": "Effect Size",
            "facet_type": "FacetType.NUMERIC",
            "description": "log2 fold changes",
            "coverage": ["Target", "Source"],
            "range": [stats.min_effect, stats.max_effect],
        },
        {
            "id": "Significance",
            "name": "Significance",
            "facet_type": "FacetType.NUMERIC",
            "description": "An adjusted p value",
            "coverage": ["Target", "Source"],
            "range64": [stats.min_sig, stats.max_sig],
        },
    ]


def default_facets() -> list[str]:
    return [
        EffectObservationDirectionType.ENRICHED.value,
        EffectObservationDirectionType.DEPLETED.value,
        EffectObservationDirectionType.BOTH.value,
    ]


class Bucket:
    class ChromKey(StrEnum):
        SOURCE = "source"
        GENE = "gene"

    def __init__(self):
        self.count = 0
        self.log10_sig = float("-infinity")
        self.effect = 0
        self.associated_buckets = set()

    def add_reo(self, reo, comp_item, filter):
        self.count += 1

        match filter.coverage_type:
            case CoverageType.COUNT:
                self.log10_sig = max(self.log10_sig, reo["log10pvalue"])
                if abs(reo["score"]) > abs(self.effect):
                    self.effect = reo["score"]
            case CoverageType.SIGNIFICANCE:
                if reo["log10pvalue"] > self.log10_sig:
                    self.log10_sig = reo["log10pvalue"]
                    self.effect = reo["score"]
            case CoverageType.EFFECT:
                if abs(reo["score"]) > abs(self.effect):
                    self.log10_sig = reo["log10pvalue"]
                    self.effect = reo["score"]

        chrom_name = reo[f"{comp_item}_chr"][3:]
        chrom_idx = CHROM_NAMES.index(chrom_name)
        bucket_size = SMALL_BUCKET_SIZE if filter.chrom is not None else LARGE_BUCKET_SIZE
        bucket = reo[f"{comp_item}_start"] // bucket_size
        self.associated_buckets.add((chrom_idx, bucket))


def chromosomes(chroms, filter):
    for chrom in chroms:
        chrom_name = chrom["chr"][3:]
        if filter.chrom is not None:
            if CHROM_NAMES[filter.chrom] != chrom_name:
                continue
            chrom_idx = 0
        else:
            chrom_idx = CHROM_NAMES.index(chrom_name)
        yield (chrom_idx, reos(chrom["reos"], filter))


def reos(reo_list, filter):
    for reo in reo_list:
        reo = reo["reo"]
        reo_pval = reo["log10pvalue"]
        reo_sig = reo["significant"]
        reo_effect = reo["score"]

        if reo_pval is None:
            continue

        if filter.numeric_intervals is not None:
            if reo_pval < filter.numeric_intervals.sig[0] or reo_pval > filter.numeric_intervals.sig[1]:
                continue

            if reo_effect < filter.numeric_intervals.effect[0] or reo_effect > filter.numeric_intervals.effect[1]:
                continue

        if filter.categorical_facets:
            cat_filter = [
                EffectObservationDirectionType.ENRICHED.value in filter.categorical_facets
                and reo_sig
                and reo_effect > 0,
                EffectObservationDirectionType.DEPLETED.value in filter.categorical_facets
                and reo_sig
                and reo_effect < 0,
                EffectObservationDirectionType.NON_SIGNIFICANT.value in filter.categorical_facets and not reo_sig,
            ]

            if not any(cat_filter):
                continue

        yield reo


class Chromosomes:
    class ReoTrack(StrEnum):
        Source = "source"
        Gene = "gene"

    def __init__(self, filter):
        self.bucket_size = SMALL_BUCKET_SIZE if filter.chrom is not None else LARGE_BUCKET_SIZE
        if filter.chrom is not None:
            self.chroms = [
                {
                    "chrom": CHROM_NAMES[filter.chrom],
                    "bucket_size": self.bucket_size,
                    "source_intervals": [],
                    "target_intervals": [],
                }
            ]
        else:
            self.chroms = [
                {"chrom": chrom, "bucket_size": self.bucket_size, "source_intervals": [], "target_intervals": []}
                for chrom in CHROM_NAMES
            ]

        self.source_buckets = defaultdict(lambda: defaultdict(Bucket))
        self.target_buckets = defaultdict(lambda: defaultdict(Bucket))
        self.filter = filter

    def gen_assoc_buckets(self, bucket):
        new_abs = []
        for ab in bucket.associated_buckets:
            new_abs.extend(ab)
        return new_abs

    def add_reo(self, chrom_idx, reo, track: ReoTrack):
        if track == Chromosomes.ReoTrack.Source:
            buckets = self.source_buckets[chrom_idx]
            comp_item = Bucket.ChromKey.GENE
        else:
            buckets = self.target_buckets[chrom_idx]
            comp_item = Bucket.ChromKey.SOURCE
        bucket = buckets[((reo[f"{track}_start"] // self.bucket_size) * self.bucket_size) + 1]
        bucket.add_reo(reo, comp_item, self.filter)

    def chrom_data(self):
        for i, chrom in enumerate(self.chroms):
            chrom["source_intervals"] = [
                {
                    "start": loc,
                    "count": b.count,
                    "associated_buckets": self.gen_assoc_buckets(b),
                    "log10_sig": b.log10_sig,
                    "effect": b.effect,
                }
                for loc, b in self.source_buckets[i].items()
            ]

            chrom["target_intervals"] = [
                {
                    "start": loc,
                    "count": b.count,
                    "associated_buckets": self.gen_assoc_buckets(b),
                    "log10_sig": b.log10_sig,
                    "effect": b.effect,
                }
                for loc, b in self.target_buckets[i].items()
            ]
        return self.chroms


class Stats:
    def __init__(self):
        self.max_sig = float("-infinity")
        self.min_sig = float("infinity")
        self.max_effect = 0
        self.min_effect = float("infinity")

        self.reo_count = 0
        self.sources = set()
        self.genes = set()

    def add_reo(self, reo, reo_value):
        reo_pval = reo["log10pvalue"]
        reo_effect = reo["score"]

        self.reo_count += reo_value
        self.sources.add((reo["source_chr"], reo["source_start"], reo["source_end"]))
        self.genes.add((reo["gene_chr"], reo["gene_start"], reo["gene_end"]))
        try:
            self.max_sig = max(self.max_sig, reo_pval)
            self.min_sig = min(self.min_sig, reo_pval)
            self.max_effect = max(self.max_effect, reo_effect)
            self.min_effect = min(self.min_effect, reo_effect)
        except Exception as e:
            logger.error(reo)
            raise e


def experiment_exists(expr_id):
    return QueryCache.objects.filter(experiment_accession_id=expr_id).exists()


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
                "name": reo["_id"],
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
              RETURN merge(rrg, { "gene_chr": g.chr, "gene_start": g.start, "gene_end": g.end, "source_chr": rr.chr, "source_start": rr.start, "source_end": rr.end, "source_annotation": rr.source_annotation })
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


def generate_data(experiment, data_filter):
    igvf_data = QueryCache.objects.filter(experiment_accession_id=experiment).order_by("-created_at").first()
    if igvf_data is None:
        update_coverage_data()
        raise GetIGVFException("No IGVF Data found. Please try again in a few minutes.")

    stats = Stats()
    chrom_data = Chromosomes(data_filter)
    for chrom_idx, reo_list in chromosomes(igvf_data.value["sources"], data_filter):
        for reo in reo_list:
            stats.add_reo(reo, 1)
            chrom_data.add_reo(chrom_idx, reo, Chromosomes.ReoTrack.Source)

    for chrom_idx, reo_list in chromosomes(igvf_data.value["genes"], data_filter):
        for reo in reo_list:
            stats.add_reo(reo, 0)
            chrom_data.add_reo(chrom_idx, reo, Chromosomes.ReoTrack.Gene)

    if stats.min_sig == float("infinity"):
        stats.min_sig = 0
    if stats.max_sig == float("-infinity"):
        stats.max_sig = 0
    if stats.min_effect == float("infinity"):
        stats.min_effect = 0

    logger.debug(stats)

    return chrom_data.chrom_data(), stats
