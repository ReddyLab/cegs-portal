import json
from collections import defaultdict

from cegs_portal.search.models import RegulatoryEffect

# {
#     "chrom": "Y",
#     "genes": [
#       {
#         "start": 1,
#         "end": 5000000,
#         "count": 2344,
#         "ccres": [
#           {
#             "index": 1,
#             "count": 2
#           }
#         ]
#       }
#     ],
#     "ccres": [
#       {
#         "start": 1,
#         "end": 5000000,
#         "count": 1000,
#         "genes": [
#           {
#             "index": 1,
#             "count": 2
#           }
#         ]
#       }
#     ]
#   },

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


def mergeSetDict(dict1, dict2):
    for k, v in dict2.items():
        temp_set = dict1.get(k, set()) | v
        dict1[k] = temp_set


def countRange(chromos, key):
    high = 0
    low = float("inf")
    for chromo in chromos:
        for value in chromo[key]:
            if value["count"] < low:
                low = value["count"]

            if value["count"] > high:
                high = value["count"]

    return [low, high]


def run(output_file, bucket_size=5_000_000):
    def bucket(start):
        return start // bucket_size

    chroms = GRCH37
    gene_buckets = {chrom: [0 for _ in range(bucket(size) + 1)] for chrom, size in chroms}
    gene_ccre_buckets = {chrom: [defaultdict(set) for _ in range(bucket(size) + 1)] for chrom, size in chroms}
    ccre_buckets = {chrom: [0 for _ in range(bucket(size) + 1)] for chrom, size in chroms}
    ccre_gene_buckets = {chrom: [defaultdict(set) for _ in range(bucket(size) + 1)] for chrom, size in chroms}
    chrom_dicts = [{"chrom": chrom, "genes": [], "ccres": []} for chrom, _ in chroms]
    print("Initialized...")
    reg_effects = RegulatoryEffect.objects.filter(experiment_id=20).prefetch_related("target_assemblies", "sources")
    print("Query built...")
    sources = set()
    genes = set()
    for reg_effect in reg_effects.all():
        source_counter = defaultdict(set)
        gene_counter = defaultdict(set)
        for source in reg_effect.sources.all():
            source_counter[bucket(source.location.lower)].add(source)

        for gene in reg_effect.target_assemblies.all():
            gene_counter[bucket(gene.location.lower)].add(source)

        for source in reg_effect.sources.all():
            chrom = source.chromosome_name[3:]
            mergeSetDict(ccre_gene_buckets[chrom][bucket(source.location.upper)], gene_counter)
            if source in sources:
                continue
            sources.add(source)
            ccre_buckets[chrom][bucket(source.location.lower)] += 1

        for gene in reg_effect.target_assemblies.all():
            chrom = gene.chrom_name[3:]
            if gene.strand == "+":
                mergeSetDict(gene_ccre_buckets[chrom][bucket(gene.location.lower)], source_counter)
            if gene.strand == "-":
                mergeSetDict(gene_ccre_buckets[chrom][bucket(gene.location.upper)], source_counter)

            if gene in genes:
                continue
            genes.add(gene)

            if gene.strand == "+":
                gene_buckets[chrom][bucket(gene.location.lower)] += 1
            if gene.strand == "-":
                gene_buckets[chrom][bucket(gene.location.upper)] += 1

    print("Buckets filled...")
    for i, chrom_info in enumerate(chroms):
        chrom, _ = chrom_info
        cd = chrom_dicts[i]
        for j, gene_bucket in enumerate(gene_buckets[chrom]):
            cd["genes"].append(
                {
                    "start": bucket_size * j + 1,
                    "end": bucket_size * (j + 1),
                    "count": gene_bucket,
                    "ccres": [{"index": k, "count": len(v)} for k, v in gene_ccre_buckets[chrom][j].items()],
                }
            )
        for j, ccre_bucket in enumerate(ccre_buckets[chrom]):
            cd["ccres"].append(
                {
                    "start": bucket_size * j + 1,
                    "end": bucket_size * (j + 1),
                    "count": ccre_bucket,
                    "genes": [{"index": k, "count": len(v)} for k, v in ccre_gene_buckets[chrom][j].items()],
                }
            )

    data = {
        "chromosomes": chrom_dicts,
        "geneCountRange": countRange(chrom_dicts, "genes"),
        "ccreCountRange": countRange(chrom_dicts, "ccres"),
    }
    with open(output_file, "w") as out:
        out.write(json.dumps(data))
