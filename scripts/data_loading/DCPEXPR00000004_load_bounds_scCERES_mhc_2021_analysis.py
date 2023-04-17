import csv

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    Analysis,
    DNAFeature,
    DNAFeatureType,
    Facet,
    FacetValue,
    RegulatoryEffectObservation,
)
from utils import AnalysisMetadata, timer

DIR_FACET = Facet.objects.get(name="Direction")
DIR_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=DIR_FACET.id).all()}

GRNA_FACET = Facet.objects.get(name="gRNA Type")
GRNA_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=GRNA_FACET.id).all()}


#
# The following lines should work as expected when using postgres. See
# https://docs.djangoproject.com/en/3.1/ref/models/querysets/#bulk-create
#
#     If the model’s primary key is an AutoField, the primary key attribute can
#     only be retrieved on certain databases (currently PostgreSQL and MariaDB 10.5+).
#     On other databases, it will not be set.
#
# So the objects won't need to be saved one-at-a-time like they are, which is slow.
#
# In postgres the objects automatically get their id's when bulk_created but
# objects that reference the bulk_created objects (i.e., with foreign keys) don't
# get their foreign keys updated. The for loops do that necessary updating.
def bulk_save(effects, effect_directions, sources, source_facets, targets):
    with transaction.atomic():
        print("Adding RegulatoryEffectObservations")
        RegulatoryEffectObservation.objects.bulk_create(effects, batch_size=1000)

    with transaction.atomic():
        print("Adding gRNA type facets to gRNA regions")
        for source, facets in zip(sources, source_facets):
            source.facet_values.add(*facets)

    with transaction.atomic():
        print("Adding effect directions to effects")
        for direction, effect in zip(effect_directions, effects):
            effect.facet_values.add(direction)

    with transaction.atomic():
        print("Adding sources to RegulatoryEffectObservations")
        for source, effect in zip(sources, effects):
            effect.sources.add(source)
        print("Adding targets to RegulatoryEffectObservations")
        for target, effect in zip(targets, effects):
            effect.targets.add(target)


# loading does buffered writes to the DB, with a buffer size of 10,000 annotations
@timer("Load Reg Effects")
def load_reg_effects(ceres_file, accession_ids, analysis, ref_genome, ref_genome_patch, delimiter=","):
    experiment = analysis.experiment
    cell_line = experiment.biosamples.first().cell_line_name
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    sources = []
    source_facets = []
    effects = []
    effect_directions = []
    target_assembiles = []
    grnas = {}
    existing_grna_facets = {}
    for i, line in enumerate(reader):
        # every other line in this file is basically a duplicate of the previous line
        if i % 2 == 0:
            continue
        grna_id = line["grna"]

        if grna_id in grnas:
            guide = grnas[grna_id]
        else:
            existing_grna_facets[grna_id] = set()

            grna_info = grna_id.split("-")

            if not grna_info[0].startswith("chr"):
                continue

            if len(grna_info) == 5:
                chrom_name, grna_start_str, _grna_end_str, _strand, _grna_seq = grna_info
            elif len(grna_info) == 6:
                chrom_name, grna_start_str, _grna_end_str, _x, _y, _grna_seq = grna_info

            grna_start = int(grna_start_str)
            grna_location = NumericRange(grna_start, grna_start + 20, "[]")

            try:
                guide = DNAFeature.objects.get(
                    misc__grna=grna_id,
                    cell_line=cell_line,
                    location=grna_location,
                    ref_genome=ref_genome,
                    ref_genome_patch=ref_genome_patch,
                    feature_type=DNAFeatureType.GRNA,
                )
            except DNAFeature.MultipleObjectsReturned as e:
                print(
                    f"{cell_line} {chrom_name}:{grna_location} {ref_genome} { ref_genome_patch} {DNAFeatureType.GRNA}"
                )
                raise e
            existing_grna_facets[grna_id].update(guide.facet_values.all())
            grnas[grna_id] = guide
        sources.append(guide)

        grna_type = line["type"]
        grna_facets = set()

        if grna_type == "targeting":
            grna_facets.add(GRNA_FACET_VALUES["Targeting"])
        elif grna_type == "nontargeting":
            grna_facets.add(GRNA_FACET_VALUES["Non-targeting"])
        elif grna_type == "positive_control_ipsc":
            grna_facets.add(GRNA_FACET_VALUES["Positive Control"])
            grna_facets.add(GRNA_FACET_VALUES["Positive Control (iPSC)"])
        elif grna_type == "positive_control_k562":
            grna_facets.add(GRNA_FACET_VALUES["Positive Control"])
            grna_facets.add(GRNA_FACET_VALUES["Positive Control (k562)"])
        elif grna_type == "positive_control_npc":
            grna_facets.add(GRNA_FACET_VALUES["Positive Control"])
            grna_facets.add(GRNA_FACET_VALUES["Positive Control (NPC)"])
        elif grna_type == "positive_control_other":
            grna_facets.add(GRNA_FACET_VALUES["Positive Control"])
            grna_facets.add(GRNA_FACET_VALUES["Positive Control (other)"])
        source_facets.append(grna_facets - existing_grna_facets[grna_id])
        existing_grna_facets[grna_id].update(grna_facets)

        significance = float(line["pval_fdr_corrected"])
        effect_size = float(line["avg_logFC"])
        if significance >= 0.01:
            direction = DIR_FACET_VALUES["Non-significant"]
        elif effect_size > 0:
            direction = DIR_FACET_VALUES["Enriched Only"]
        elif effect_size < 0:
            direction = DIR_FACET_VALUES["Depleted Only"]
        else:
            direction = DIR_FACET_VALUES["Non-significant"]

        try:
            target_assembly = DNAFeature.objects.get(ref_genome=ref_genome, ensembl_id=line["gene_stable_id"])
        except DNAFeature.DoesNotExist as e:
            print(f'"{ref_genome}", "{line["gene_stable_id"]}"')
            raise e

        effect = RegulatoryEffectObservation(
            accession_id=accession_ids.incr(AccessionType.REGULATORY_EFFECT_OBS),
            experiment=experiment,
            experiment_accession=experiment,
            analysis=analysis,
            facet_num_values={
                RegulatoryEffectObservation.Facet.EFFECT_SIZE.value: effect_size,
                RegulatoryEffectObservation.Facet.RAW_P_VALUE.value: float(line["p_val"]),
                RegulatoryEffectObservation.Facet.SIGNIFICANCE.value: significance,
            },
        )
        target_assembiles.append(target_assembly)
        effects.append(effect)
        effect_directions.append(direction)
    bulk_save(effects, effect_directions, sources, source_facets, target_assembiles)


def unload_reg_effects(analysis_metadata):
    analysis = Analysis.objects.get(
        experiment_id=analysis_metadata.experiment_accession_id, name=analysis_metadata.name
    )
    RegulatoryEffectObservation.objects.filter(analysis=analysis).delete()
    analysis_metadata.db_del(analysis)


def check_filename(analysis_filename: str):
    if len(analysis_filename) == 0:
        raise ValueError(f"scCERES analysis filename '{analysis_filename}' must not be blank")


def run(analysis_filename):
    with open(analysis_filename) as analysis_file:
        analysis_metadata = AnalysisMetadata.json_load(analysis_file)
    check_filename(analysis_metadata.name)

    # Only run unload_reg_effects if you want to delete the analysis, all
    # associated reg effects, and any DNAFeatures created from the DB.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_reg_effects() uncommented is not, strictly, idempotent.
    # unload_reg_effects(analysis_metadata)

    analysis = analysis_metadata.db_save()

    with AccessionIds(message=f"{analysis.accession_id}: {analysis.name}"[:200]) as accession_ids:
        for ceres_file, file_info, delimiter in analysis_metadata.metadata():
            load_reg_effects(
                ceres_file,
                accession_ids,
                analysis,
                file_info.ref_genome,
                file_info.ref_genome_patch,
                delimiter,
            )
