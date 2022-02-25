import json
from collections import defaultdict
from os.path import join

from django.db.models import Prefetch
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNARegion, FeatureAssembly, RegulatoryEffect

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


def mergeSetDict(dict1, dict2):
    for k, v in dict2.items():
        temp_set = dict1.get(k, set()) | v
        dict1[k] = temp_set


def countRange(chromo, key):
    high = 0
    low = float("inf")
    for value in chromo[key]:
        if value["count"] < low:
            low = value["count"]

        if value["count"] > high:
            high = value["count"]

    return [low, high]


def run(output_dir, chrom, bucket_size=100_000):
    def bucket(start):
        return start // bucket_size

    chroms = GRCH37
    start = 1
    end = 1
    for chrom_name, length in chroms:
        if chrom == chrom_name:
            end = length
    chrom_id = chrom
    chrom_size = [c for c in chroms if c[0] == chrom_id][0][1]
    gene_buckets = [0 for _ in range(bucket(chrom_size) + 1)]
    gene_ccre_buckets = [defaultdict(set) for _ in range(bucket(chrom_size) + 1)]
    ccre_buckets = [0 for _ in range(bucket(chrom_size) + 1)]
    ccre_gene_buckets = [defaultdict(set) for _ in range(bucket(chrom_size) + 1)]
    chrom_dicts = {"genes": [], "ccres": []}
    print("Initialized...")
    dnaRegions = DNARegion.objects.filter(
        chromosome_name=f"chr{chrom}", location__overlap=NumericRange(int(start), int(end), "[)")
    )
    featureAssemblies = FeatureAssembly.objects.filter(
        chrom_name=f"chr{chrom}", location__overlap=NumericRange(int(start), int(end), "[)")
    )
    reg_effects = RegulatoryEffect.objects.filter(experiment_id=20).prefetch_related(
        Prefetch("target_assemblies", queryset=featureAssemblies), Prefetch("sources", queryset=dnaRegions)
    )
    print("Query built...")
    sources = set()
    genes = set()
    for reg_effect in reg_effects.all():
        source_counter = defaultdict(set)
        gene_counter = defaultdict(set)

        for source in reg_effect.sources.all():
            source_counter[bucket(source.location.lower)].add(source)

        for gene in reg_effect.target_assemblies.all():
            gene_counter[bucket(gene.location.lower)].add(gene)

        for gene in reg_effect.target_assemblies.all():
            if gene.strand == "+":
                mergeSetDict(gene_ccre_buckets[bucket(gene.location.lower)], source_counter)
            if gene.strand == "-":
                mergeSetDict(gene_ccre_buckets[bucket(gene.location.upper)], source_counter)

            if gene in genes:
                continue
            genes.add(gene)

            if gene.strand == "+":
                gene_buckets[bucket(gene.location.lower)] += 1
            if gene.strand == "-":
                gene_buckets[bucket(gene.location.upper)] += 1

        for source in reg_effect.sources.all():
            mergeSetDict(ccre_gene_buckets[bucket(source.location.upper)], gene_counter)

            if source in sources:
                continue
            sources.add(source)

            ccre_buckets[bucket(source.location.lower)] += 1

    print("Buckets filled...")
    for i, gene_bucket in enumerate(gene_buckets):
        chrom_dicts["genes"].append(
            {
                "start": bucket_size * i + 1,
                "end": bucket_size * (i + 1),
                "count": gene_bucket,
                "ccres": [{"index": k, "count": len(v)} for k, v in gene_ccre_buckets[i].items()],
            }
        )
    for i, ccre_bucket in enumerate(ccre_buckets):
        chrom_dicts["ccres"].append(
            {
                "start": bucket_size * i + 1,
                "end": bucket_size * (i + 1),
                "count": ccre_bucket,
                "genes": [{"index": k, "count": len(v)} for k, v in ccre_gene_buckets[i].items()],
            }
        )

    data = {
        "chromosome": chrom,
        "start": start,
        "end": end,
        "genes": chrom_dicts["genes"],
        "ccres": chrom_dicts["ccres"],
        "geneCountRange": countRange(chrom_dicts, "genes"),
        "ccreCountRange": countRange(chrom_dicts, "ccres"),
    }
    with open(join(output_dir, f"level2_{chrom}.json"), "w") as out:
        out.write(json.dumps(data))
