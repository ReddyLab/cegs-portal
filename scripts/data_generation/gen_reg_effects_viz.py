import json
import time
from collections import defaultdict
from os.path import join

from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation

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


def run(output_dir, chrom, bucket_size=100_000):
    chroms = GRCH37
    start = 1
    chrom_end = 1
    end = start + bucket_size
    for chrom_name, length in chroms:
        if chrom == chrom_name:
            chrom_end = length
    chrom_name = f"chr{chrom}"
    print("Initialized...")
    reg_effects = RegulatoryEffectObservation.objects.filter(experiment_id=20).prefetch_related(
        "targets",
        "targets__children",
        "targets__children__children",
        "sources",
    )
    fbt = time.perf_counter()
    while start < chrom_end:
        sources = set()
        targets = set()
        gene_dhs = defaultdict(set)
        featureAssemblies = DNAFeature.objects.filter(
            chrom_name=chrom_name, location__overlap=NumericRange(int(start), int(end), "[)")
        )
        local_reg_effects = reg_effects.filter(targets__in=featureAssemblies)

        for reg_effect in local_reg_effects.all():
            source_set = set(reg_effect.sources.all())
            target_set = set(reg_effect.targets.all())
            sources |= source_set
            targets |= target_set
            for target in target_set:
                gene_dhs[target] |= source_set

        data = {
            "chromosome": chrom,
            "start": start,
            "end": end,
            "genes": [],
            "ccres": [[source.location.lower, source.location.upper] for source in sources],
        }
        target_list = []
        for target in targets:
            gene_start = target.location.lower if target.strand == "+" else target.location.upper

            if gene_start < start or gene_start >= end:
                continue

            tx_list = []
            for tx in target.children.all():
                exon_list = []
                for exon in tx.children.all():
                    exon_list.append([exon.location.lower, exon.location.upper])
                tx_list.append(
                    {
                        "strand": tx.strand,
                        "start": tx.location.lower if tx.strand == "+" else tx.location.upper,
                        "end": tx.location.upper if tx.strand == "+" else tx.location.lower,
                        "exons": exon_list,
                    }
                )
            target_list.append(
                {
                    "name": target.name,
                    "strand": target.strand,
                    "start": gene_start,
                    "end": target.location.upper if target.strand == "+" else target.location.lower,
                    "tx": tx_list,
                    "ccres": [[dhs.location.lower, dhs.location.upper] for dhs in gene_dhs[target]],
                }
            )
        data["targets"] = target_list

        with open(join(output_dir, f"level3_{chrom_name}_{start}_{end}.json"), "w") as out:
            out.write(json.dumps(data))

        start = end
        end = min(chrom_end, start + bucket_size)
    print(f"finished with {chrom_name}: {time.perf_counter() - fbt}s")
