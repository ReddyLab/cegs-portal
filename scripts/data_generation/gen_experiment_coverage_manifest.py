import json
import pickle
from os.path import join

from utils import flatten


def load_coverage(output_dir):
    level1_filename = join(output_dir, "level1.pkl")
    with open(level1_filename, "rb") as level1_file:
        level1 = pickle.load(level1_file)
    return level1


def display_transform(data):
    result = {"chromosomes": [], "facets": data["facets"]}
    for chromosome in data["chromosomes"]:
        chrom_data = {
            "chrom": chromosome["chrom"],
            "bucket_size": chromosome["bucket_size"],
            "source_intervals": [],
            "target_intervals": [],
        }

        for interval in chromosome["source_intervals"]:
            new_interval = {"start": interval["start"], "count": len(interval["sources"])}

            targets = set()
            for source in interval["sources"]:
                targets.update(source[1])

            new_interval["assoc_targets"] = flatten(list(targets))
            chrom_data["source_intervals"].append(new_interval)

        for interval in chromosome["target_intervals"]:
            new_interval = {"start": interval["start"], "count": len(interval["targets"])}

            sources = set()
            for target in interval["targets"]:
                sources.update(target[1])

            new_interval["assoc_sources"] = flatten(list(sources))
            chrom_data["target_intervals"].append(new_interval)

        result["chromosomes"].append(chrom_data)

    return result


def run(output_location, genome):
    level1_data = load_coverage(output_location)
    display_data = display_transform(level1_data)

    if genome == "GRCH38":
        genome_file = "grch38.json"
    elif genome == "GRCH37":
        genome_file = "grch38.json"
    else:
        raise Exception(f'Invalid genome {genome}. Must be "GRCH37" or "GRCH38"')

    display_data["genome"] = genome_file

    with open(join(output_location, "coverage_manifest.json"), "w") as out:
        out.write(json.dumps(display_data))
