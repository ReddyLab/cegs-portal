import json
import time
from collections import defaultdict
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

#  Output json format:
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
#                [<number of continuous facet ids>, <continuous list of number of discrete facet ids, discrete facet ids, effect size, and significance for each source in this bucket>], # noqa: E501
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
#                [<number of continuous facet ids>, <continuous list of number of discrete facet ids, discrete facet ids, effect size, and significance for each source in this bucket>], # noqa: E501
#                [<bucket indexes containing reg-effect associated targets>]
#              ],
#              ...
#            ]
#          },
#          ...
#        ]
#      }
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


def flatten(list_):
    result = []
    for item in list_:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def run(output_dir, experiment_accession_id, chrom, genome, bucket_size=100_000):
    def bucket(start):
        return start // bucket_size

    if genome == "GRCH38":
        chroms = GRCH38
    elif genome == "GRCH37":
        chroms = GRCH37
    else:
        raise Exception(f'Invalid genome {genome}. Must be "GRCH37" or "GRCH38"')
    chrom_size = [c for c in chroms if c[0] == chrom][0][1]
    chrom_keys = {chrom[0]: i for i, chrom in enumerate(chroms)}
    target_buckets = [dict() for _ in range(bucket(chrom_size) + 1)]
    source_buckets = [dict() for _ in range(bucket(chrom_size) + 1)]
    chrom_dict = {"chrom": chrom, "bucket_size": bucket_size, "target_intervals": [], "source_intervals": []}
    print(f"chr{chrom} Initialized...")
    dna_regions = DNARegion.objects.filter(chrom_name=f"chr{chrom}")
    feature_assemblies = FeatureAssembly.objects.filter(chrom_name=f"chr{chrom}")
    reg_effects = (
        RegulatoryEffect.objects.with_facet_values()
        .filter(experiment__accession_id=experiment_accession_id, target_assemblies__chrom_name=f"chr{chrom}")
        .order_by("id")
        .prefetch_related(
            Prefetch("target_assemblies", queryset=feature_assemblies),
            Prefetch("sources", queryset=dna_regions),
            Prefetch("sources__facet_values"),
            Prefetch("sources__facet_values__facet"),
        )
    )
    direction_facet_id = Facet.objects.get(name=RegulatoryEffect.Facet.DIRECTION.value).id
    ccre_overlap_facet_id = Facet.objects.get(name=DNARegion.Facet.DHS_CCRE_OVERLAP_CATEGORIES.value).id
    ccre_category_facet_id = Facet.objects.get(name=DNARegion.Facet.CCRE_CATEGORIES.value).id
    grna_type_facet_id = Facet.objects.get(name=DNARegion.Facet.GRNA_TYPE.value).id
    print("Query built...")
    sources = set()
    fbt = time.perf_counter()

    facet_ids = set()
    re_count = reg_effects.count()
    print(f"Effect Count: {re_count}")
    SKIP = 10000
    five_pct_rc = re_count * 0.05
    pct_rc = five_pct_rc
    for start in range(0, re_count, SKIP):
        stop = min(start + SKIP, re_count)
        if start > pct_rc:
            print(f"Percent complete: {(start / re_count) * 100:.0f}% ({time.perf_counter() - fbt:.0f} s)")
            pct_rc = start + five_pct_rc
        for reg_effect in reg_effects.all()[start:stop]:
            sources = reg_effect.sources.all()
            targets = reg_effect.target_assemblies.all()
            source_counter = defaultdict(set)
            reg_disc_facets = [v.id for v in reg_effect.facet_values.all() if v.facet_id == direction_facet_id]
            source_disc_facets = set()
            target_disc_facets = set()
            target_counter = defaultdict(set)

            for source in sources:
                source_counter[(source.chrom_name[3:], bucket(source.location.lower))].add(source)
                source_disc_facets.update(
                    [v.id for v in source.facet_values.all() if v.facet_id == ccre_category_facet_id]
                )
                source_disc_facets.update(
                    [v.id for v in source.facet_values.all() if v.facet_id == ccre_overlap_facet_id]
                )
                source_disc_facets.update([v.id for v in source.facet_values.all() if v.facet_id == grna_type_facet_id])

            for target in targets:
                if target.strand == "+":
                    target_start = target.location.lower

                if target.strand == "-":
                    target_start = target.location.upper

                target_counter[(target.chrom_name[3:], bucket(target_start))].add(target)

                target_dict = target_buckets[bucket(target_start)].get(target.name, [[2], set()])
                disc_facets = [*reg_disc_facets, *source_disc_facets]
                target_dict[0].extend(
                    [
                        len(disc_facets),
                        *disc_facets,
                        reg_effect.effect_size,
                        reg_effect.significance,
                    ]
                )
                target_dict[1].update(source_counter.keys())
                target_buckets[bucket(target_start)][target.name] = target_dict

            for source in sources:
                coords = (source.location.lower, source.location.upper)

                source_dict = source_buckets[bucket(source.location.lower)].get(
                    coords, [[2], set()]
                )  # 2 is the number of continuous facets
                disc_facets = [*reg_disc_facets, *target_disc_facets]
                disc_facets.extend([v.id for v in source.facet_values.all() if v.facet_id == ccre_category_facet_id])
                disc_facets.extend([v.id for v in source.facet_values.all() if v.facet_id == ccre_overlap_facet_id])
                disc_facets.extend([v.id for v in source.facet_values.all() if v.facet_id == grna_type_facet_id])

                source_dict[0].extend(
                    [
                        len(disc_facets),
                        *disc_facets,
                        reg_effect.effect_size,
                        reg_effect.significance,
                    ]
                )
                source_dict[1].update(target_counter.keys())
                source_buckets[bucket(source.location.lower)][coords] = source_dict

            facet_ids.update(reg_disc_facets)
            facet_ids.update(source_disc_facets)
            facet_ids.update(target_disc_facets)

    print(f"Buckets filled... {time.perf_counter() - fbt} s")
    for j, target_bucket in enumerate(target_buckets):
        if len(target_bucket) == 0:
            continue

        chrom_dict["target_intervals"].append(
            {
                "start": bucket_size * j + 1,
                "targets": [
                    [
                        info[0],
                        flatten([[chrom_keys[chrom], bucket] for chrom, bucket in info[1]]),
                    ]
                    for _, info in target_bucket.items()
                ],
            }
        )
    for j, source_bucket in enumerate(source_buckets):
        if len(source_bucket) == 0:
            continue

        chrom_dict["source_intervals"].append(
            {
                "start": bucket_size * j + 1,
                "sources": [
                    [
                        info[0],
                        flatten([[chrom_keys[chrom], bucket] for chrom, bucket in info[1]]),
                    ]
                    for _, info in source_bucket.items()
                ],
            }
        )

    facets = []
    # These are the facets we use for this data
    experiment_facets = {
        "Direction": ["target", "source"],
        "Effect Size": ["target", "source"],
        "Source Category": ["target", "source"],
        "Source Overlap": ["target", "source"],
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
        "chromosomes": [chrom_dict],
        "facets": facets,
    }

    with open(join(output_dir, f"level2_{chrom}.json"), "w") as out:
        out.write(json.dumps(data))
