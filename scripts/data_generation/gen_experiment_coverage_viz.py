import pickle
import time
from os.path import join

from django.db.models import FloatField, Max, Min, Prefetch
from django.db.models.functions import Cast

from cegs_portal.search.models import (
    DNARegion,
    Facet,
    FacetType,
    FeatureAssembly,
    RegulatoryEffect,
)

#  Output object format:
#  {
#    "bucket_size": <bucket_size parameter value>,
#    "chromosomes": [
#      {
#        "chrom": <chromosome number>,
#        "target_intervals": [
#          {
#            "start": <start position, 1-indexed>,
#            "targets": [
#              [
#                [<number of continuous facet ids>, <continuous list of number of discrete facet ids, discrete facet ids, effect size, and significance for each gene in this bucket>], # noqa: E501
#                [<bucket indexes containing reg-effect associated sources>]
#              ],
#              ...
#            ],
#          },
#          ...
#        ],
#        "source_intervals": [
#          {
#            "start": <start position, 1-indexed>,
#            "sources": [
#              [
#                [<number of continuous facet ids>, <continuous list of number of discrete facet ids, discrete facet ids, effect size, and significance for each ccre in this bucket>], # noqa: E501
#                [<bucket indexes containing reg-effect associated targets>]
#              ],
#              ...
#            ]
#          },
#          ...
#        ]
#      },
#      ...
#    ],
#    "facets": [
#      {
#        "name": <facet name>,
#        "description": <facet description>,
#        "type": <FacetType.DISCRETE or FacetType.CONTINUOUS>,
#        "values": { <id>: <value> },  # if discrete
#        "range": [<start>, <end>]  # if continuous
#      }
#    ]
# }
#

GRCH38 = [
    ("1", 248956422),
    ("2", 242193529),
    ("3", 198295559),
    ("4", 190214555),
    ("5", 181538259),
    ("6", 170805979),
    ("7", 159345973),
    ("8", 145138636),
    ("9", 138394717),
    ("10", 133797422),
    ("11", 135086622),
    ("12", 133275309),
    ("13", 114364328),
    ("14", 107043718),
    ("15", 101991189),
    ("16", 90338345),
    ("17", 83257441),
    ("18", 80373285),
    ("19", 58617616),
    ("20", 64444167),
    ("21", 46709983),
    ("22", 50818468),
    ("X", 156040895),
    ("Y", 57227415),
    ("MT", 16569),
]
GRCH37 = [
    ("1", 249250621),
    ("2", 243199373),
    ("3", 198022430),
    ("4", 191154276),
    ("5", 180915260),
    ("6", 171115067),
    ("7", 159138663),
    ("8", 146364022),
    ("9", 141213431),
    ("10", 135534747),
    ("11", 135006516),
    ("12", 133851895),
    ("13", 115169878),
    ("14", 107349540),
    ("15", 102531392),
    ("16", 90354753),
    ("17", 81195210),
    ("18", 78077248),
    ("19", 59128983),
    ("20", 63025520),
    ("21", 48129895),
    ("22", 51304566),
    ("X", 155270560),
    ("Y", 59373566),
    ("MT", 16569),
]


def run(output_location, experiment_accession_id, genome, bucket_size=2_000_000, chrom=None):
    def bucket(start):
        return start // bucket_size

    if genome == "GRCH38":
        chroms = GRCH38
    elif genome == "GRCH37":
        chroms = GRCH37
    else:
        raise Exception(f'Invalid genome {genome}. Must be "GRCH37" or "GRCH38"')

    chrom_keys = {chrom_info[0]: i for i, chrom_info in enumerate(chroms)}

    if chrom is None:
        print("Initialized...")
        reg_effects = (
            RegulatoryEffect.objects.with_facet_values()
            .filter(experiment__accession_id=experiment_accession_id)
            .order_by("id")
            .prefetch_related("targets", "sources", "sources__facet_values", "sources__facet_values__facet")
        )
    else:
        long_chrom_name = f"chr{chrom}"
        chroms = [chrom_info for chrom_info in chroms if chrom_info[0] == chrom]
        print(f"{long_chrom_name} Initialized...")
        dna_regions = DNARegion.objects.filter(chrom_name=long_chrom_name)
        feature_assemblies = FeatureAssembly.objects.filter(chrom_name=long_chrom_name)
        reg_effects = (
            RegulatoryEffect.objects.with_facet_values()
            .filter(experiment__accession_id=experiment_accession_id, targets__chrom_name=long_chrom_name)
            .order_by("id")
            .prefetch_related(
                Prefetch("targets", queryset=feature_assemblies),
                Prefetch("sources", queryset=dna_regions),
                Prefetch("sources__facet_values"),
                Prefetch("sources__facet_values__facet"),
            )
        )

    target_buckets = {chrom_name: [dict() for _ in range(bucket(size) + 1)] for chrom_name, size in chroms}
    source_buckets = {chrom_name: [dict() for _ in range(bucket(size) + 1)] for chrom_name, size in chroms}
    chrom_dicts = [
        {"chrom": chrom_name, "bucket_size": bucket_size, "target_intervals": [], "source_intervals": []}
        for chrom_name, _ in chroms
    ]
    direction_facet_id = Facet.objects.get(name=RegulatoryEffect.Facet.DIRECTION.value).id
    ccre_overlap_facet_id = Facet.objects.get(name=DNARegion.Facet.DHS_CCRE_OVERLAP_CATEGORIES.value).id
    ccre_category_facet_id = Facet.objects.get(name=DNARegion.Facet.CCRE_CATEGORIES.value).id
    grna_type_facet_id = Facet.objects.get(name=DNARegion.Facet.GRNA_TYPE.value).id
    print("Query built...")
    fbt = time.perf_counter()

    facet_ids = set()
    re_count = reg_effects.count()
    print(f"Effect Count: {re_count}")
    SKIP = 500000
    pct_rc = five_pct_rc = re_count * 0.05
    for start in range(0, re_count, SKIP):
        stop = min(start + SKIP, re_count)
        if start > pct_rc:
            print(f"Percent complete: {(start / re_count) * 100:.0f}% ({time.perf_counter() - fbt:.0f} s)")
            pct_rc = start + five_pct_rc
        for reg_effect in reg_effects.all()[start:stop]:
            sources = reg_effect.sources.all()
            targets = reg_effect.targets.all()

            # If we are targeting a specific chromosome filter out sources not in that chromosome.
            # They won't be visible in the visualization and the bucket index will be wrong.
            if chrom is not None:
                sources = [source for source in sources if source.chrom_name == long_chrom_name]

            source_counter = set()
            target_counter = set()

            reg_disc_facets = {v.id for v in reg_effect.facet_values.all() if v.facet_id == direction_facet_id}
            source_disc_facets = set()
            target_disc_facets = set()

            for source in sources:
                source_counter.add((chrom_keys[source.chrom_name[3:]], bucket(source.location.lower)))
                source_disc_facets.update(
                    [v.id for v in source.facet_values.all() if v.facet_id == ccre_category_facet_id]
                )
                source_disc_facets.update(
                    [v.id for v in source.facet_values.all() if v.facet_id == ccre_overlap_facet_id]
                )
                source_disc_facets.update([v.id for v in source.facet_values.all() if v.facet_id == grna_type_facet_id])

            for target in targets:
                chrom_name = target.chrom_name[3:]

                if target.strand == "+":
                    target_start = target.location.lower

                if target.strand == "-":
                    target_start = target.location.upper

                target_counter.add((chrom_keys[chrom_name], bucket(target_start)))

                target_info = target_buckets[chrom_name][bucket(target_start)].get(target.id, ([], set()))
                target_info[0].append(
                    (reg_disc_facets | source_disc_facets, reg_effect.effect_size, reg_effect.significance)
                )
                target_info[1].update(source_counter)
                target_buckets[chrom_name][bucket(target_start)][target.id] = target_info

            for source in sources:
                chrom_name = source.chrom_name[3:]

                disc_facets = reg_disc_facets | target_disc_facets
                disc_facets |= {
                    v.id
                    for v in source.facet_values.all()
                    if v.facet_id == ccre_category_facet_id
                    or v.facet_id == ccre_overlap_facet_id
                    or v.facet_id == grna_type_facet_id
                }

                source_info = source_buckets[chrom_name][bucket(source.location.lower)].get(source.id, ([], set()))
                source_info[0].append((disc_facets, reg_effect.effect_size, reg_effect.significance))
                source_info[1].update(target_counter)
                source_buckets[chrom_name][bucket(source.location.lower)][source.id] = source_info

            facet_ids.update(reg_disc_facets)
            facet_ids.update(source_disc_facets)
            facet_ids.update(target_disc_facets)

    print(f"Buckets filled... {time.perf_counter() - fbt} s")
    for i, chrom_info in enumerate(chroms):
        chrom_name, _ = chrom_info
        cd = chrom_dicts[i]
        for j, target_bucket in enumerate(target_buckets[chrom_name]):
            if len(target_bucket) == 0:
                continue

            cd["target_intervals"].append(
                {
                    "start": bucket_size * j + 1,
                    "targets": list(target_bucket.values()),
                }
            )
        for j, source_bucket in enumerate(source_buckets[chrom_name]):
            if len(source_bucket) == 0:
                continue

            cd["source_intervals"].append(
                {
                    "start": bucket_size * j + 1,
                    "sources": list(source_bucket.values()),
                }
            )

    facets = []
    # These are the facets we use for this data
    experiment_facets = {
        "Direction": ["target", "source"],
        "Effect Size": ["target", "source"],
        "cCRE Category": ["target", "source"],
        "cCRE Overlap": ["target", "source"],
        "Significance": ["target", "source"],
        "gRNA Type": ["target", "source"],
    }
    experiment_facet_names = {name for name in experiment_facets}

    for facet in Facet.objects.all():
        if facet.name not in experiment_facet_names:
            continue

        facet_dict = {
            "name": facet.name,
            "description": facet.description,
            "type": facet.facet_type,
            "coverage": experiment_facets[facet.name],
        }

        if facet.facet_type == str(FacetType.DISCRETE):
            facet_values = {fv.id: fv.value for fv in facet.values.all() if fv.id in facet_ids}
            if len(facet_values) == 0:
                continue
            facet_dict["values"] = facet_values
        elif facet.name == "Effect Size":
            min_val = reg_effects.aggregate(min=Min(Cast("facet_num_values__Effect Size", output_field=FloatField())))
            max_val = reg_effects.aggregate(max=Max(Cast("facet_num_values__Effect Size", output_field=FloatField())))
            facet_dict["range"] = [min_val["min"], max_val["max"]]
        elif facet.name == "Significance":
            min_val = reg_effects.aggregate(min=Min(Cast("facet_num_values__Significance", output_field=FloatField())))
            max_val = reg_effects.aggregate(max=Max(Cast("facet_num_values__Significance", output_field=FloatField())))
            facet_dict["range"] = [min_val["min"], max_val["max"]]
        facets.append(facet_dict)

    data = {
        "chromosomes": chrom_dicts,
        "facets": facets,
    }

    if chrom is None:
        with open(output_location, "wb") as out:
            pickle.dump(data, out)
    else:
        with open(join(output_location, f"level2_{chrom}.pkl"), "wb") as out:
            pickle.dump(data, out)
