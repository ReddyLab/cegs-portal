import json
import time
from collections import defaultdict
from os.path import join

from django.db.models import Max, Min, Prefetch

from cegs_portal.search.models import (
    DNARegion,
    Facet,
    FacetType,
    FacetValue,
    FeatureAssembly,
    RegulatoryEffect,
)

#  Output json format:
#  {
#    "bucket_size": <bucket_size parameter value>,
#    "chromosomes": [
#      {
#        "chrom": <chromosome number>,
#        "gene_intervals": [
#          {
#            "start": <start position, 1-indexed>,
#            "genes": [
#              [
#                [<continuous list of effect direction id, effect size, and significance for each gene in this bucket>],
#                [<bucket indexes containing reg-effect associated ccres>]
#              ],
#              ...
#            ],
#          },
#          ...
#        ],
#        "ccre_intervals": [
#          {
#            "start": <start position, 1-indexed>,
#            "ccres": [
#              [
#                [<continuous list of effect direction id, effect size, and significance for each ccre in this bucket>],
#                [<bucket indexes containing reg-effect associated genes>]
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
    ("10", 133_797_422),
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


def run(output_dir, chrom, bucket_size=100_000):
    def bucket(start):
        return start // bucket_size

    def minmax(numbers):
        min_num = min(numbers)
        max_num = max(numbers)
        return [min_num, max_num]

    chroms = GRCH37
    chrom_size = [c for c in chroms if c[0] == chrom][0][1]
    gene_buckets = [dict() for _ in range(bucket(chrom_size) + 1)]
    ccre_buckets = [dict() for _ in range(bucket(chrom_size) + 1)]
    chrom_dict = {"chrom": chrom, "gene_intervals": [], "ccre_intervals": []}
    print("Initialized...")
    dna_regions = DNARegion.objects.filter(chromosome_name=f"chr{chrom}")
    feature_assemblies = FeatureAssembly.objects.filter(chrom_name=f"chr{chrom}")
    reg_effects = (
        RegulatoryEffect.objects.with_facet_values()
        .filter(experiment_id=20)
        .prefetch_related(
            Prefetch("target_assemblies", queryset=feature_assemblies), Prefetch("sources", queryset=dna_regions)
        )
    )
    print("Query built...")
    sources = set()
    fbt = time.perf_counter()

    for reg_effect in reg_effects.all():
        sources = reg_effect.sources.all()
        genes = reg_effect.target_assemblies.all()
        source_counter = defaultdict(set)
        gene_counter = defaultdict(set)

        for source in sources:
            source_counter[bucket(source.location.lower)].add(source)

        for gene in genes:
            if gene.strand == "+":
                gene_start = gene.location.lower

            if gene.strand == "-":
                gene_start = gene.location.upper

            gene_counter[bucket(gene_start)].add(gene)

            gene_dict = gene_buckets[bucket(gene_start)].get(gene.name, [[], set()])
            gene_dict[0].extend(
                [
                    reg_effect.direction_id,
                    reg_effect.effect_size,
                    reg_effect.significance,
                ]
            )
            gene_dict[1].update(source_counter.keys())
            gene_buckets[bucket(gene_start)][gene.name] = gene_dict

        for source in sources:
            coords = (source.location.lower, source.location.upper)

            ccre_dict = ccre_buckets[bucket(source.location.lower)].get(coords, [[], set()])
            ccre_dict[0].extend(
                [
                    reg_effect.direction_id,
                    reg_effect.effect_size,
                    reg_effect.significance,
                ]
            )
            ccre_dict[1].update(gene_counter.keys())
            ccre_buckets[bucket(source.location.lower)][coords] = ccre_dict

    print(f"Buckets filled... {time.perf_counter() - fbt} s")
    for j, gene_bucket in enumerate(gene_buckets):
        if len(gene_bucket) == 0:
            continue

        chrom_dict["gene_intervals"].append(
            {
                "start": bucket_size * j + 1,
                "genes": [
                    [
                        info[0],
                        list(info[1]),
                    ]
                    for _, info in gene_bucket.items()
                ],
            }
        )
    for j, ccre_bucket in enumerate(ccre_buckets):
        if len(ccre_bucket) == 0:
            continue

        chrom_dict["ccre_intervals"].append(
            {
                "start": bucket_size * j + 1,
                "ccres": [
                    [
                        info[0],
                        list(info[1]),
                    ]
                    for _, info in ccre_bucket.items()
                ],
            }
        )

    facets = []
    for facet in Facet.objects.all():
        facet_dict = {}
        facet_dict["name"] = facet.name
        facet_dict["description"] = facet.description
        facet_dict["type"] = facet.facet_type
        if facet.facet_type == str(FacetType.DISCRETE):
            facet_dict["values"] = [fv.value for fv in facet.values.all()]
        elif facet.facet_type == str(FacetType.CONTINUOUS):
            min_val = (
                FacetValue.objects.filter(facet=facet, regulatoryeffect__in=reg_effects)
                .all()
                .aggregate(Min("num_value"))
            )
            max_val = (
                FacetValue.objects.filter(facet=facet, regulatoryeffect__in=reg_effects)
                .all()
                .aggregate(Max("num_value"))
            )
            facet_dict["range"] = [min_val["num_value__min"], max_val["num_value__max"]]
        facets.append(facet_dict)

    data = {
        "bucket_size": bucket_size,
        "chromosomes": [chrom_dict],
        "facets": facets,
    }

    with open(join(output_dir, f"level2_{chrom}.json"), "w") as out:
        out.write(json.dumps(data))
