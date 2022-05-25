import json
import time
from collections import defaultdict

from django.db.models import FloatField, Max, Min
from django.db.models.functions import Cast

from cegs_portal.search.models import Facet, FacetType, RegulatoryEffect

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


def run(output_file, experiment_accession_id, bucket_size=5_000_000):
    def bucket(start):
        return start // bucket_size

    chroms = GRCH37
    target_buckets = {chrom: [dict() for _ in range(bucket(size) + 1)] for chrom, size in chroms}
    source_buckets = {chrom: [dict() for _ in range(bucket(size) + 1)] for chrom, size in chroms}
    chrom_dicts = [
        {"chrom": chrom, "bucket_size": bucket_size, "target_intervals": [], "source_intervals": []}
        for chrom, _ in chroms
    ]
    print("Initialized...")
    reg_effects = (
        RegulatoryEffect.objects.with_facet_values()
        .filter(experiment__accession_id=experiment_accession_id)
        .prefetch_related("target_assemblies", "sources", "sources__facet_values")
    )
    print("Query built...")
    sources = set()
    fbt = time.perf_counter()

    for reg_effect in reg_effects.all():
        sources = reg_effect.sources.all()
        targets = reg_effect.target_assemblies.all()
        source_counter = defaultdict(set)
        reg_disc_facets = [reg_effect.direction_id]
        source_disc_facets = []
        target_disc_facets = []
        target_counter = defaultdict(set)

        for source in sources:
            source_counter[bucket(source.location.lower)].add(source)
            source_disc_facets.extend([*source.ccre_category_ids, source.ccre_overlap_id])

        for target in targets:
            chrom = target.chrom_name[3:]

            if target.strand == "+":
                target_start = target.location.lower

            if target.strand == "-":
                target_start = target.location.upper

            target_counter[bucket(target_start)].add(target)

            target_dict = target_buckets[chrom][bucket(target_start)].get(target.name, [[2], set()])
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
            target_buckets[chrom][bucket(target_start)][target.name] = target_dict

        for source in sources:
            chrom = source.chrom_name[3:]
            coords = (source.location.lower, source.location.upper)

            source_dict = source_buckets[chrom][bucket(source.location.lower)].get(
                coords, [[2], set()]
            )  # 2 is the number of continuous facets
            disc_facets = [*reg_disc_facets, *source.ccre_category_ids, source.ccre_overlap_id, *target_disc_facets]
            source_dict[0].extend(
                [
                    len(disc_facets),
                    *disc_facets,
                    reg_effect.effect_size,
                    reg_effect.significance,
                ]
            )
            source_dict[1].update(target_counter.keys())
            source_buckets[chrom][bucket(source.location.lower)][coords] = source_dict

    print(f"Buckets filled... {time.perf_counter() - fbt} s")
    for i, chrom_info in enumerate(chroms):
        chrom, _ = chrom_info
        cd = chrom_dicts[i]
        for j, target_bucket in enumerate(target_buckets[chrom]):
            if len(target_bucket) == 0:
                continue

            cd["target_intervals"].append(
                {
                    "start": bucket_size * j + 1,
                    "targets": [
                        [
                            info[0],
                            list(info[1]),
                        ]
                        for _, info in target_bucket.items()
                    ],
                }
            )
        for j, source_bucket in enumerate(source_buckets[chrom]):
            if len(source_bucket) == 0:
                continue

            cd["source_intervals"].append(
                {
                    "start": bucket_size * j + 1,
                    "sources": [
                        [
                            info[0],
                            list(info[1]),
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
        "cCRE Category": ["target", "source"],
        "cCRE Overlap": ["target", "source"],
        "Significance": ["target", "source"],
    }
    experiment_facet_names = {name for name in experiment_facets.keys()}

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
            facet_dict["values"] = {fv.id: fv.value for fv in facet.values.all()}
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
    with open(output_file, "w") as out:
        out.write(json.dumps(data))
