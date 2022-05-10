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
#        "gene_intervals": [
#          {
#            "start": <start position, 1-indexed>,
#            "genes": [
#              [
#                [<number of continuous facet ids>, <continuous list of number of discrete facet ids, discrete facet ids, effect size, and significance for each ccre in this bucket>], # noqa: E501
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
#                [<number of continuous facet ids>, <continuous list of number of discrete facet ids, discrete facet ids, effect size, and significance for each ccre in this bucket>], # noqa: E501
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


def run(output_dir, chrom, bucket_size=100_000):
    def bucket(start):
        return start // bucket_size

    chroms = GRCH37
    chrom_size = [c for c in chroms if c[0] == chrom][0][1]
    gene_buckets = [dict() for _ in range(bucket(chrom_size) + 1)]
    ccre_buckets = [dict() for _ in range(bucket(chrom_size) + 1)]
    chrom_dict = {"chrom": chrom, "bucket_size": bucket_size, "gene_intervals": [], "ccre_intervals": []}
    print("Initialized...")
    dna_regions = DNARegion.objects.filter(chrom_name=f"chr{chrom}")
    feature_assemblies = FeatureAssembly.objects.filter(chrom_name=f"chr{chrom}")
    reg_effects = (
        RegulatoryEffect.objects.with_facet_values()
        .filter(experiment__accession_id="DCPE00000002")
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
        reg_disc_facets = [reg_effect.direction_id]
        source_disc_facets = []
        target_disc_facets = []
        gene_counter = defaultdict(set)

        for source in sources:
            source_counter[bucket(source.location.lower)].add(source)
            source_disc_facets.extend([*source.ccre_category_ids, source.ccre_overlap_id])

        for gene in genes:
            if gene.strand == "+":
                gene_start = gene.location.lower

            if gene.strand == "-":
                gene_start = gene.location.upper

            gene_counter[bucket(gene_start)].add(gene)

            gene_dict = gene_buckets[bucket(gene_start)].get(gene.name, [[2], set()])
            disc_facets = [*reg_disc_facets, *source_disc_facets]
            gene_dict[0].extend(
                [
                    len(disc_facets),
                    *disc_facets,
                    reg_effect.effect_size,
                    reg_effect.significance,
                ]
            )
            gene_dict[1].update(source_counter.keys())
            gene_buckets[bucket(gene_start)][gene.name] = gene_dict

        for source in sources:
            coords = (source.location.lower, source.location.upper)

            ccre_dict = ccre_buckets[bucket(source.location.lower)].get(
                coords, [[2], set()]
            )  # 2 is the number of continuous facets
            disc_facets = [*reg_disc_facets, *source.ccre_category_ids, source.ccre_overlap_id, *target_disc_facets]
            ccre_dict[0].extend(
                [
                    len(disc_facets),
                    *disc_facets,
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
    # These are the facets we use for this data
    experiment_facets = {
        "Direction": ["gene", "ccre"],
        "Effect Size": ["gene", "ccre"],
        "cCRE Category": ["gene", "ccre"],
        "cCRE Overlap": ["gene", "ccre"],
        "Significance": ["gene", "ccre"],
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
        "chromosomes": [chrom_dict],
        "facets": facets,
    }

    with open(join(output_dir, f"level2_{chrom}.json"), "w") as out:
        out.write(json.dumps(data))
