#!/usr/bin/env python

import argparse
import csv
import re
import time
from dataclasses import dataclass
from typing import Optional, TypeAlias

import requests

JSON_MIME = "application/json"

URLString: TypeAlias = str
CSRFToken: TypeAlias = str


def is_url(path: str):
    return path.startswith("https://") or path.startswith("http://")


@dataclass(init=False)
class Metadata:
    accession_id: str
    experiment_metadata_url: Optional[str] = None
    experiment_metadata_file: Optional[str] = None
    analysis_metadata_url: Optional[str] = None
    analysis_metadata_file: Optional[str] = None

    def __init__(self, accession_id, experiment_path: Optional[str], analysis_path: Optional[str]):
        self.accession_id = accession_id

        if experiment_path is not None:
            if is_url(experiment_path):
                self.experiment_metadata_url = experiment_path
            else:
                self.experiment_metadata_file = experiment_path

        if analysis_path is not None:
            if is_url(analysis_path):
                self.analysis_metadata_url = analysis_path
            else:
                self.analysis_metadata_file = analysis_path

    def __str__(self):
        experiment = (
            self.experiment_metadata_file if self.experiment_metadata_file is not None else self.experiment_metadata_url
        )
        analysis = (
            self.analysis_metadata_file if self.analysis_metadata_file is not None else self.analysis_metadata_url
        )
        return f"{self.accession_id}: {experiment} {analysis}"


class UploadSession:
    hostname: URLString
    login_url: URLString
    upload_url: URLString
    status_url: URLString
    csrf_token: CSRFToken

    def __init__(self, hostname):
        self.hostname = hostname
        self.login_url = f"{hostname}/accounts/login/"
        self.upload_url = f"{hostname}/uploads/"
        self.status_url = f"{hostname}/task_status/task/"
        self.session = None

    def __enter__(self):
        self.session = requests.Session()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def _check_response_status(self, response: requests.Response):
        if not response.ok:
            raise RuntimeError(f"Bad Response Code: {response.status_code} ({response.request.method} {response.url})")

    def _get_login_csrf(self):
        r = self.session.get(self.login_url)
        self._check_response_status(r)
        self.csrf_token = r.cookies["csrftoken"]

    def login(self, username, password):
        self._get_login_csrf()
        login = self.session.post(
            self.login_url,
            data={
                "csrfmiddlewaretoken": self.csrf_token,
                "login": username,
                "password": password,
            },
            headers={"Referer": self.login_url},
        )
        self._check_response_status(login)
        self.csrf_token = login.cookies["csrftoken"]

    def upload(self, metadata: list[Metadata]):
        for metadatum in metadata:
            print(f"Uploading {metadatum}")
            data = {
                "csrfmiddlewaretoken": self.csrf_token,
                "accept": JSON_MIME,
                "experiment_accession": metadatum.accession_id,
            }
            files = {}

            #
            # Add the experiment and analysis metadata to the request as appropriate
            #
            if metadatum.experiment_metadata_file is not None:
                if isinstance(metadatum.experiment_metadata_file, str):
                    files["experiment_file"] = open(metadatum.experiment_metadata_file, encoding="utf-8")

            if metadatum.experiment_metadata_url is not None:
                if isinstance(metadatum.experiment_metadata_url, str):
                    data["experiment_url"] = metadatum.experiment_metadata_url

            if metadatum.analysis_metadata_file is not None:
                if isinstance(metadatum.analysis_metadata_file, str):
                    files["analysis_file"] = open(metadatum.analysis_metadata_file, encoding="utf-8")

            if metadatum.analysis_metadata_url is not None:
                if isinstance(metadatum.analysis_metadata_url, str):
                    data["analysis_url"] = metadatum.analysis_metadata_url

            #
            # Upload the metadata
            #
            upload = self.session.post(
                self.upload_url,
                data=data,
                files=files,
                headers={"Referer": self.login_url},
            )
            self._check_response_status(upload)
            result_json = upload.json()

            task_status_id = result_json["task_status_id"]

            if (file := files.get("experiment_file")) is not None:
                file.close()
            if (file := files.get("analysis_file")) is not None:
                file.close()

            #
            # Check the status until the upload is finished or errors out
            #
            statuses = set()
            while True:
                status_result = self.session.get(f"{self.status_url}{task_status_id}", params={"accept": JSON_MIME})
                self._check_response_status(status_result)
                status_result = status_result.json()
                status = status_result["status"]

                match status:
                    case "W":
                        message = "Waiting to Start"
                    case "S":
                        message = "Started"
                    case "F":
                        message = "Finished Successfully"
                    case "E":
                        message = f"Error: {status_result['error_message']}"

                if status not in statuses:
                    print(message)
                    statuses.add(status)

                match status:
                    case "F" | "E":
                        break
                    case _:
                        pass

                time.sleep(3)


def full_hostname(hostname: str) -> URLString:
    if hostname[-1] == "/":
        hostname = hostname[:-1]

    if is_url(hostname):
        return hostname

    return f"http://{hostname}"


def next_accession(accession: str) -> str:
    match = re.fullmatch(r"DCPEXPR([\da-fA-F]{10})", accession)
    number = int(match.group(1), base=16) + 1

    return f"DCPEXPR{number:010X}"


# TSV of metadata:
#
# Accession ID\texperiment metadata\tanalysis metadata
#
# If an accession id is not set, use the previous accession id + 1
# Skip blank lines
# Skip lines that start with '#'
# experiment and analysis files are optional
#
def read_metadata_list(metadata_file: str) -> list[Metadata]:
    metadata = []
    prev_accession = None
    with open(metadata_file, encoding="utf-8") as metadata_tsv:
        reader = csv.reader(metadata_tsv, delimiter="\t")
        for row in reader:
            # Skip if the row doesn't have the right number of columns
            try:
                accession, experiment_path, analysis_path = row
            except ValueError:
                continue

            # skip if the row is blank, minus the tabs
            if accession == experiment_path == analysis_path == "":
                continue

            # skip if the row is commented out
            if accession.startswith("#"):
                continue

            # If the row doesn't define an accession ID figure out what
            # it should be
            if accession in ["", None]:
                assert prev_accession is not None
                accession = next_accession(prev_accession)

            prev_accession = accession

            if len(experiment_path) == 0:
                experiment_path = None

            if len(analysis_path) == 0:
                analysis_path = None

            metadata.append(
                Metadata(
                    accession_id=accession,
                    experiment_path=experiment_path,
                    analysis_path=analysis_path,
                )
            )

    return metadata


def get_metadata(args: argparse.Namespace) -> list[Metadata]:
    if args.file is not None:
        metadata = read_metadata_list(args.file)
    else:
        metadata = [
            Metadata(
                accession_id=args.accession,
                experiment_path=args.ef,
                analysis_path=args.af,
            )
        ]
    return metadata


def get_args():
    parser = argparse.ArgumentParser(description="A script for bulk-uploading experiments/screens to the CCGR Portal")
    parser.add_argument("host", help="Portal hostname")
    parser.add_argument("-u", "--username", help="Username", required=True)
    parser.add_argument("-p", "--password", help="Password", required=True)

    bulk = parser.add_argument_group(title="Bulk Experiment/Analysis Upload")
    bulk.add_argument(
        "-f",
        "--file",
        help="A TSV containing locations of the experiment/analysis metadata needed to load the data",
    )

    single = parser.add_argument_group(title="Single Experiment/Analysis Upload")
    single.add_argument("-a", "--accession", help="The experiment accession ID")
    single.add_argument("--ef", "--experiment-file", help="The experiment metadata")
    single.add_argument("--af", "--analysis-file", help="The analysis metadata")

    ns = parser.parse_args()

    if getattr(ns, "file", None) is not None and (
        getattr(ns, "accession", None) is not None
        or getattr(ns, "ef", None) is not None
        or getattr(ns, "af", None) is not None
    ):
        parser.error("Bulk (-f) and Single (-a, --ef, --af) Uploads are mututally exclusive")

    return ns


def main(args: argparse.Namespace):
    host = full_hostname(args.host)
    metadata = get_metadata(args)

    with UploadSession(host) as session:
        session.login(args.username, args.password)
        session.upload(metadata)


if __name__ == "__main__":
    parsed_args = get_args()
    main(parsed_args)
