import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from io import StringIO
from os import SEEK_SET
from typing import Optional

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    DNAFeature,
    DNAFeatureType,
    EffectObservationDirectionType,
    Experiment,
    Facet,
    FacetValue,
    RegulatoryEffectObservation,
)
from utils.db_ids import ReoIds

from .db import bulk_reo_save, cat_facet_entry, reo_entry, source_entry, target_entry
from .experiment_metadata import AnalysisMetadata, InternetFile
from .types import Facets, FeatureType

MIN_SIG = 1e-100


@dataclass
class FeatureInfo:
    name: Optional[str]
    chrom_name: str
    start: int
    end: int
    bounds: str


@dataclass
class SourceInfo:
    chrom: str
    start: int
    end: int
    bounds: str
    strand: Optional[str]
    feature_type: FeatureType

    def __post_init__(self):
        DNAFeatureType(self.feature_type)

        if self.strand == ".":
            self.strand = None


@dataclass
class ObservationRow:
    sources: list[SourceInfo]
    targets: list[str]  # ensembl ids
    categorical_facets: list[str]
    numeric_facets: dict[str:float]


class Analysis:
    metadata: AnalysisMetadata
    observations: Optional[list[ObservationRow]] = None
    accession_id: Optional[str] = None

    def __init__(self, metadata: AnalysisMetadata):
        self.metadata = metadata

        dir_facet = Facet.objects.get(name="Direction")
        self.categorical_facet_values = {
            facet.value: facet.id for facet in FacetValue.objects.filter(facet_id=dir_facet.id).all()
        }

    def load(self):
        match self.metadata.data_format:
            case "standard":
                return self._load_standard()
            case "jesse-engreitz":
                return self._load_jesse_engreitz()

    def _load_standard(self):
        source_type = self.metadata.source_type

        results_file = self.metadata.results
        results_tsv = InternetFile(results_file.file_location).file
        reader = csv.DictReader(results_tsv, delimiter=results_file.delimiter(), quoting=csv.QUOTE_NONE)
        observations: list[ObservationRow] = []
        for line in reader:
            chrom_name, start, end, strand, bounds = (
                line["chrom"],
                int(line["start"]),
                int(line["end"]),
                line["strand"],
                line["bounds"],
            )
            sources = [SourceInfo(chrom_name, start, end, bounds, strand, source_type)]

            targets = [line["gene_ensembl_id"]]

            raw_p_value = float(line["raw_p_val"])
            adjusted_p_value = float(line["adj_p_val"])
            effect_size = float(line["effect_size"])
            categorical_facets = [f.split("=") for f in line["facets"].split(";")] if line["facets"] != "" else []

            for _, facet_value in categorical_facets:
                if facet_value not in self.categorical_facet_values:
                    raise ValueError(f"Invalid categorical facet value: '{facet_value}'")

            num_facets = {
                Facets.EFFECT_SIZE: effect_size,
                Facets.SIGNIFICANCE: adjusted_p_value,
                Facets.RAW_P_VALUE: raw_p_value,
            }

            observations.append(ObservationRow(sources, targets, categorical_facets, num_facets))

        results_tsv.close()
        self.observations = observations
        return self

    def _load_jesse_engreitz(self):
        # The analysis data requires 4 files from the ENCODE data set:
        # 1) element quantifications aka results_file
        # 2) elements reference (guides) aka element_file
        # 3) elements reference (DHS peaks) aka parent_element_file
        # 4) a guide quantifications file aka guide_quant_file
        #
        # Loading the files requires compiling data from all four files. The element quantifications (1) file
        # Tells us which peaks DHS peaks from the elements reference (3) to include. The elements reference (3)
        # includes all the oligo ids for a given DHS peak which we can use to get the guids from elements references (2).
        # Unfortunately, elements reference (2) doesn't have the strand information! For this we need one of the guide
        # quantification files. We can match the guide in (2) to the guide information in (4) via the guide sequence.
        #
        # Once we have all the guide information we can match the guide (source) to the observation and target information
        # which are in the element quantifications (1) file.

        source_type = self.metadata.source_type

        #
        # Much like when loading the experiment we have to use the results file to figure out which DHS peaks to include
        #
        results_file = self.metadata.results.file_metadata
        results_tsv = InternetFile(results_file.file_location).file
        results_reader = csv.DictReader(results_tsv, delimiter=results_file.delimiter(), quoting=csv.QUOTE_NONE)
        result_targets = {
            f'{line["chrPerturbationTarget"]}:{line["startPerturbationTarget"]}-{line["endPerturbationTarget"]}'
            for line in results_reader
        }

        #
        # Match DHS Peaks to oligo ids and create a set of all oligo ids
        #
        parent_element_file = self.metadata.misc_files[1]
        parent_element_tsv = InternetFile(parent_element_file.file_location).file
        parent_reader = csv.DictReader(
            parent_element_tsv, delimiter=parent_element_file.delimiter(), quoting=csv.QUOTE_NONE
        )
        parent_elements = defaultdict(set)
        parent_oligos = set()
        for line in parent_reader:
            if line["target"] in result_targets:
                parent_elements[line["target"]].add(line["OligoID"])
                parent_oligos.add(line["OligoID"])

        #
        # Get all guides associated with DHS peaks
        #
        element_file = self.metadata.misc_files[0]
        element_tsv = InternetFile(element_file.file_location).file
        element_reader = csv.DictReader(element_tsv, delimiter=element_file.delimiter(), quoting=csv.QUOTE_NONE)
        elements = {}
        for e in element_reader:
            if e["OligoID"] not in parent_oligos:
                continue

            elements[e["OligoID"]] = (e["chr"], int(e["start"]), int(e["end"]), e["GuideSequence"])

        #
        # Get strands for guides
        #
        guide_quant_file = self.metadata.misc_files[2]
        quide_quant_tsv = InternetFile(guide_quant_file.file_location).file
        guide_quant_reader = csv.reader(quide_quant_tsv, delimiter=guide_quant_file.delimiter(), quoting=csv.QUOTE_NONE)
        chrom_strands = ["+", "-"]
        guide_strands = {}
        for line in guide_quant_reader:
            if line[5] in chrom_strands:
                guide_strands[line[14]] = line[5]
            else:
                guide_strands[line[14]] = None

        #
        # Go back through the results, matching guides to observations using the parent_elements dictionary
        #
        results_tsv.seek(0, SEEK_SET)
        results_reader = csv.DictReader(results_tsv, delimiter=results_file.delimiter(), quoting=csv.QUOTE_NONE)
        observations: list[ObservationRow] = []
        for line in results_reader:
            chrom_name, start, end = (
                line["chrPerturbationTarget"],
                int(line["startPerturbationTarget"]),
                int(line["endPerturbationTarget"]),
            )
            parent_element = f"{chrom_name}:{start}-{end}"
            oligos = parent_elements[parent_element]
            sources = []

            for oligo in oligos:
                guide_chrom, guide_start, guide_end, guide_seq = elements[oligo]

                # We previously filtered out guides invalid strands
                # Here, we skip over those guides
                if guide_seq in guide_strands:
                    sources.append(
                        SourceInfo(guide_chrom, guide_start, guide_end, "[)", guide_strands[guide_seq], source_type)
                    )

            if len(sources) == 0:
                continue

            targets = [line["measuredEnsemblID"]]

            raw_p_value = float(line["pValue"])
            adjusted_p_value = float(line["pValueAdjusted"])
            # An explanation of the effect size values, from an email with Ben Doughty:
            #
            # For the effect size calculations, since we do a 6-bin sort, we don't actually compute a log2-fold change.
            # Instead, we use the data to compute an effect size in "gene expression" space, which we normalize to the
            # negative controls. The values are then scaled, so what an effect size of -0.2 means is that this guide
            # decreased the expression of the target gene by 20%. An effect size of 0 would be no change in expression,
            # and an effect size of +0.1 would mean a 10% increase in expression. The lowest we can go is -1 (which means
            # total elimination of signal), and technically the effect size is unbounded in the positive direction,
            # although we never see _super_ strong positive guides with CRISPRi.
            effect_size = float(line["EffectSize"])

            num_facets = {
                Facets.EFFECT_SIZE: effect_size,
                Facets.SIGNIFICANCE: adjusted_p_value,
                Facets.RAW_P_VALUE: raw_p_value,
            }

            if adjusted_p_value <= self.metadata.results.p_val_threshold:
                if effect_size > 0:
                    cat_facets = [
                        (
                            RegulatoryEffectObservation.Facet.DIRECTION.value,
                            EffectObservationDirectionType.ENRICHED.value,
                        )
                    ]
                else:
                    cat_facets = [
                        (
                            RegulatoryEffectObservation.Facet.DIRECTION.value,
                            EffectObservationDirectionType.DEPLETED.value,
                        )
                    ]
            else:
                cat_facets = [
                    (
                        RegulatoryEffectObservation.Facet.DIRECTION.value,
                        EffectObservationDirectionType.NON_SIGNIFICANT.value,
                    )
                ]

            observations.append(ObservationRow(sources, targets, cat_facets, num_facets))

        results_tsv.close()
        element_tsv.close()
        parent_element_tsv.close()
        quide_quant_tsv.close()
        self.observations = observations
        return self

    def _save_reos(self, accession_ids):
        if self.observations is None:
            return

        analysis_accession_id = self.accession_id
        experiment_accession_id = self.metadata.experiment_accession_id
        experiment_id = Experiment.objects.filter(accession_id=experiment_accession_id).values_list("id", flat=True)[0]
        genome_assembly = self.metadata.genome_assembly
        sources = StringIO()
        targets = StringIO()
        effects = StringIO()
        cat_facets = StringIO()
        source_cache = {}
        target_cache = {}

        with ReoIds() as reo_ids:
            for reo_id, reo in zip(reo_ids, self.observations):
                for source in reo.sources:
                    source_string = f"{source.chrom}:{source.start}-{source.end}:{source.strand}:{genome_assembly}"
                    if source_string not in source_cache:
                        source_cache[source_string] = DNAFeature.objects.filter(
                            experiment_accession_id=experiment_accession_id,
                            chrom_name=source.chrom,
                            location=NumericRange(source.start, source.end, source.bounds),
                            strand=source.strand,
                            ref_genome=genome_assembly,
                            feature_type=DNAFeatureType(source.feature_type),
                        ).values_list("id", flat=True)[0]

                    sources.write(source_entry(reo_id, source_cache[source_string]))

                for target in reo.targets:
                    if target not in target_cache:
                        target_cache[target] = DNAFeature.objects.filter(
                            ref_genome=genome_assembly, ensembl_id=target
                        ).values_list("id", flat=True)[0]

                    targets.write(target_entry(reo_id, target_cache[target]))

                facet_num_values = {
                    RegulatoryEffectObservation.Facet(key).value: value for key, value in reo.numeric_facets.items()
                }

                if Facets.LOG_SIGNIFICANCE not in facet_num_values:
                    facet_num_values[RegulatoryEffectObservation.Facet.LOG_SIGNIFICANCE.value] = -math.log10(
                        max(reo.numeric_facets[Facets.SIGNIFICANCE], MIN_SIG)
                    )
                effects.write(
                    reo_entry(
                        id_=reo_id,
                        accession_id=accession_ids.incr(AccessionType.REGULATORY_EFFECT_OBS),
                        experiment_id=experiment_id,
                        experiment_accession_id=experiment_accession_id,
                        analysis_accession_id=analysis_accession_id,
                        facet_num_values=facet_num_values,
                    )
                )

                for _, facet_value in reo.categorical_facets:
                    facet_id = self.categorical_facet_values[facet_value]
                    cat_facets.write(cat_facet_entry(reo_id, facet_id))

        bulk_reo_save(effects, cat_facets, sources, targets)

    def save(self):
        with transaction.atomic():
            analysis = self.metadata.db_save()
            self.accession_id = analysis.accession_id

            with AccessionIds(message=f"{self.accession_id}: {self.metadata.name}"[:200]) as accession_ids:
                self._save_reos(accession_ids)

        return self


def load(analysis_filename, experiment_accession_id):
    metadata = AnalysisMetadata.load(analysis_filename, experiment_accession_id)
    analysis = Analysis(metadata).load().save()
    return analysis.accession_id
