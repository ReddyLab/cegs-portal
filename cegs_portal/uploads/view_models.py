import re

from cegs_portal.search.models import Experiment


def next_accession(accession: str) -> str:
    match = re.fullmatch(r"DCPEXPR([\da-fA-F]{10})", accession)
    number = int(match.group(1), base=16) + 1

    return f"DCPEXPR{number:010X}"


def add_experiment_to_user(experiment_accession, user):
    user.experiments.append(experiment_accession)
    user.save()


def get_next_experiment_accession() -> str:
    largest_accession = Experiment.objects.all().values_list("accession_id", flat=True).order_by("-id").first()
    return "DCPEXPR0000000000" if largest_accession is None else next_accession(largest_accession)
