import json
import time
from collections import defaultdict

from django.db.models import Max, Min

from cegs_portal.search.models import Facet, FacetType, FacetValue, RegulatoryEffect

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


def run(output_file, bucket_size=5_000_000):
    def bucket(start):
        return start // bucket_size

    def minmax(numbers):
        min_num = min(numbers)
        max_num = max(numbers)
        return [min_num, max_num]

    chroms = GRCH37
    gene_buckets = {chrom: [dict() for _ in range(bucket(size) + 1)] for chrom, size in chroms}
    ccre_buckets = {chrom: [dict() for _ in range(bucket(size) + 1)] for chrom, size in chroms}
    chrom_dicts = [{"chrom": chrom, "gene_intervals": [], "ccre_intervals": []} for chrom, _ in chroms]
    print("Initialized...")
    reg_effects = (
        RegulatoryEffect.objects.with_facet_values()
        .filter(experiment_id=20)
        .prefetch_related("target_assemblies", "sources")
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

        for gene in genes:
            chrom = gene.chrom_name[3:]

            if gene.strand == "+":
                gene_start = gene.location.lower

            if gene.strand == "-":
                gene_start = gene.location.upper

            gene_dict = gene_buckets[chrom][bucket(gene_start)].get(
                gene.name, {"d": set(), "e": [], "s": [], "sr": set()}
            )
            gene_dict["d"].add(reg_effect.direction)
            gene_dict["e"].append(reg_effect.effect_size)
            gene_dict["s"].append(reg_effect.significance)
            gene_dict["sr"].update(source_counter.keys())
            gene_buckets[chrom][bucket(gene_start)][gene.name] = gene_dict

        for source in sources:
            chrom = source.chromosome_name[3:]
            coords = (source.location.lower, source.location.upper)

            ccre_dict = ccre_buckets[chrom][bucket(source.location.lower)].get(
                coords, {"d": set(), "e": [], "s": [], "tg": set()}
            )
            ccre_dict["d"].add(reg_effect.direction)
            ccre_dict["e"].append(reg_effect.effect_size)
            ccre_dict["s"].append(reg_effect.significance)
            ccre_dict["tg"].update(gene_counter.keys())
            ccre_buckets[chrom][bucket(source.location.lower)][coords] = ccre_dict

    # for query in [{"sql": q["sql"][0:min(512, len(q["sql"]))], "time": q["time"]} for q in connection.queries]:
    #     print(query)

    print(f"Buckets filled... {time.perf_counter() - fbt} s")
    for i, chrom_info in enumerate(chroms):
        chrom, _ = chrom_info
        cd = chrom_dicts[i]
        for j, gene_bucket in enumerate(gene_buckets[chrom]):
            if len(gene_bucket) == 0:
                continue

            cd["gene_intervals"].append(
                {
                    "start": bucket_size * j + 1,
                    "end": bucket_size * (j + 1),
                    "genes": [
                        {
                            "d": list(info["d"]),
                            "e": minmax(info["e"]),
                            "s": minmax(info["s"]),
                            "sr": list(info["sr"]),
                        }
                        for _, info in gene_bucket.items()
                    ],
                }
            )
        for j, ccre_bucket in enumerate(ccre_buckets[chrom]):
            if len(ccre_bucket) == 0:
                continue

            cd["ccre_intervals"].append(
                {
                    "start": bucket_size * j + 1,
                    "end": bucket_size * (j + 1),
                    "ccres": [
                        {
                            "d": list(info["d"]),
                            "e": minmax(info["e"]),
                            "s": minmax(info["s"]),
                            "tg": list(info["tg"]),
                        }
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
        "chromosomes": chrom_dicts,
        "facets": facets,
    }
    with open(output_file, "w") as out:
        out.write(json.dumps(data))
