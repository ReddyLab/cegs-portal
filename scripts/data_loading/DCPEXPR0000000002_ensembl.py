import csv

from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNAFeature
from utils.experiment import ExperimentMetadata

from .load_experiment import Experiment


def run(experiment_filename):
    metadata = ExperimentMetadata.file_load(experiment_filename)
    exp = Experiment(metadata)

    dhs_file = exp.metadata.tested_elements_file
    genome_assembly = dhs_file.genome_assembly

    genes = {}
    with open(dhs_file.filename, "r") as feature_tsv:
        reader = csv.DictReader(feature_tsv, delimiter=dhs_file.delimiter(), quoting=csv.QUOTE_NONE)
        for line in reader:
            gene_name = line["gene_symbol"]
            gene_start = int(line["start"]) - 1
            gene_end = int(line["end"])
            gene_location = NumericRange(gene_start, gene_end, "[)")
            if gene_name not in genes:
                gene_objects = DNAFeature.objects.filter(
                    name=gene_name, location=gene_location, ref_genome=genome_assembly
                ).all()

                if len(gene_objects) == 1:
                    gene = gene_objects[0]
                    genes[gene_name] = gene.ensembl_id
                elif len(gene_objects) == 0:
                    # This case shouldn't happen
                    genes[gene_name] = None
                else:
                    # There is ONE instance where there are two genes with the same name
                    # in the exact same location. This handles that situation.
                    # The two gene IDs are ENSG00000272333 and ENSG00000105663.
                    # I decided that ENSG00000272333 was the "correct" gene to use here
                    # because it's the one that still exists in hg38.
                    genes[gene_name] = "ENSG00000272333"

    with open("genes.txt", "w") as output:
        for key, value in genes.items():
            output.write(f"{key}\t{value}\n")
