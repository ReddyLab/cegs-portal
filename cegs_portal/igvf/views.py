import logging
import time
from datetime import datetime, timedelta, timezone

from arango.client import ArangoClient
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.views.generic import View
from huey.contrib.djhuey import db_task

from cegs_portal.igvf.models import QueryCache

logger = logging.getLogger(__name__)

HOSTNAME = "https://db.catalog.igvf.org"
DB_NAME = "igvf"
HEADERS = {"Content-Type": "application/json"}
PAYLOAD = {"username": "guest", "password": "guestigvfcatalog"}


@db_task()
def update_coverage_data():
    client = ArangoClient(hosts=HOSTNAME)
    db = client.db(DB_NAME, username=PAYLOAD["username"], password=PAYLOAD["password"])
    async_db = db.begin_async_execution(return_result=True)

    query = async_db.aql.execute(
        """
        LET reos = (
            FOR rr IN genomic_elements
            FOR g in genes
            FOR rrg IN genomic_elements_genes
              FILTER rrg._to == g._id && rrg._from == rr._id && HAS(rrg, "significant")
              RETURN merge(rrg, { "gene_chr": g.chr, "gene_start": g.`start`, "gene_end": g.`end`, "source_chr": rr.chr, "source_start": rr.`start`, "source_end": rr.`end`  })
        )

        LET sources = (FOR reo IN reos
        COLLECT chr = reo.source_chr INTO groups
        RETURN { "chr": chr, "reos": groups})

        LET genes = (FOR reo IN reos
        COLLECT chr = reo.gene_chr INTO groups
        RETURN { "chr": chr, "reos": groups})

        RETURN {"sources": sources, "genes": genes}
    """
    )

    if query is None:
        return

    logger.debug("IGVF Query started")
    # Let's wait until the jobs are finished.
    while query.status() != "done":
        logger.debug("IGVF Query working")
        time.sleep(10)

    logger.debug(f"IGVF Query complete: {query.status()}")
    result = query.result().pop()

    cache = QueryCache(value=result)
    cache.save()


class CoverageView(View):
    def get(self, request, *args, **kwargs):
        igvf_data = QueryCache.objects.all().order_by("-created_at").first()
        if igvf_data is None:
            update_coverage_data()
            return HttpResponseServerError("No IGVF Data found. Please try again in a few minutes.")

        logger.debug(f"now offset: {(datetime.now(timezone.utc) - timedelta(days=15)).utcoffset()}")
        logger.debug(f"created offset: {igvf_data.created_at.utcoffset()}")
        if igvf_data.created_at < (datetime.now(timezone.utc) - timedelta(days=15)):
            update_coverage_data()

        return render(request, "coverage.html", {"coverage": igvf_data.value})
