import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum, StrEnum
from typing import Optional

from arango.client import ArangoClient
from django.http import HttpResponseServerError, JsonResponse
from django.shortcuts import render
from django.views.generic import View
from huey.contrib.djhuey import db_task

from cegs_portal.igvf.models import QueryCache
from cegs_portal.search.models import EffectObservationDirectionType
from cegs_portal.utils.http_exceptions import Http400

logger = logging.getLogger(__name__)

HOSTNAME = "https://db.catalog.igvf.org"
DB_NAME = "igvf"
HEADERS = {"Content-Type": "application/json"}
PAYLOAD = {"username": "guest", "password": "guestigvfcatalog"}
BUCKET_SIZE = 2000000
CHROM_NAMES = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "X",
    "Y",
    "MT",
]


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


class CoverageType(Enum):
    COUNT = 0
    SIGNIFICANCE = 1
    EFFECT = 2


@dataclass
class FilterIntervals:
    effect: tuple[float, float]
    sig: tuple[float, float]


@dataclass
class Filter:
    categorical_facets: set[str]
    chrom: Optional[int]
    coverage_type: CoverageType
    numeric_intervals: Optional[FilterIntervals]


def get_filter(filters, chrom, coverage_type):
    if chrom is not None:
        chrom = CHROM_NAMES.index(chrom)

    if len(filters) > 1:
        effect_size_interval, sig_interval = filters[1]
        numeric_intervals = FilterIntervals(
            effect=(effect_size_interval[0], effect_size_interval[1]), sig=(sig_interval[0], sig_interval[1])
        )
    else:
        numeric_intervals = None

    match coverage_type:
        case "coverage-type-count":
            coverage_type = CoverageType.COUNT
        case "coverage-type-sig":
            coverage_type = CoverageType.SIGNIFICANCE
        case "coverage-type-effect":
            coverage_type = CoverageType.EFFECT
        case _:
            coverage_type = CoverageType.COUNT

    return Filter(
        categorical_facets=set(filters[0]),
        chrom=chrom,
        numeric_intervals=numeric_intervals,
        coverage_type=coverage_type,
    )


def view_facets(stats):
    return [
        {
            "id": "Direction",
            "name": "Direction",
            "facet_type": "FacetType.CATEGORICAL",
            "description": "Effect change direction",
            "coverage": ["Target", "Source"],
            "values": {
                "Depleted Only": "Depleted Only",
                "Enriched Only": "Enriched Only",
                "Non-significant": "Non-significant",
            },
        },
        {
            "id": "Effect Size",
            "name": "Effect Size",
            "facet_type": "FacetType.NUMERIC",
            "description": "log2 fold changes",
            "coverage": ["Target", "Source"],
            "range": [stats["min_effect"], stats["max_effect"]],
        },
        {
            "id": "Significance",
            "name": "Significance",
            "facet_type": "FacetType.NUMERIC",
            "description": "An adjusted p value",
            "coverage": ["Target", "Source"],
            "range64": [stats["min_sig"], stats["max_sig"]],
        },
    ]


def default_facets() -> list[str]:
    return [
        EffectObservationDirectionType.ENRICHED.value,
        EffectObservationDirectionType.DEPLETED.value,
        EffectObservationDirectionType.BOTH.value,
    ]


class Bucket:
    class ChromKey(StrEnum):
        SOURCE = "source"
        GENE = "gene"

    def __init__(self):
        self.count = 0
        self.log10_sig = float("-infinity")
        self.effect = 0
        self.associated_buckets = set()

    def add_reo(self, reo, comp_item, coverage_type):
        self.count += 1

        match coverage_type:
            case CoverageType.COUNT:
                self.log10_sig = max(self.log10_sig, reo["log10pvalue"])
                if abs(reo["score"]) > abs(self.effect):
                    self.effect = reo["score"]
            case CoverageType.SIGNIFICANCE:
                if reo["log10pvalue"] > self.log10_sig:
                    self.log10_sig = reo["log10pvalue"]
                    self.effect = reo["score"]
            case CoverageType.EFFECT:
                if abs(reo["score"]) > abs(self.effect):
                    self.log10_sig = reo["log10pvalue"]
                    self.effect = reo["score"]

        chrom_name = reo[f"{comp_item}_chr"][3:]
        chrom_idx = CHROM_NAMES.index(chrom_name)
        bucket = reo[f"{comp_item}_start"] // BUCKET_SIZE
        self.associated_buckets.add((chrom_idx, bucket))


def gen_chroms(igvf_value, filter):
    def gen_assoc_buckets(bucket):
        new_abs = []
        for ab in bucket.associated_buckets:
            new_abs.extend(ab)
        return new_abs

    chroms = [
        {"chrom": chrom, "bucket_size": BUCKET_SIZE, "source_intervals": [], "target_intervals": []}
        for chrom in CHROM_NAMES
    ]

    reos_sources = igvf_value["sources"]
    reos_genes = igvf_value["genes"]

    for chrom in reos_sources:
        buckets = defaultdict(Bucket)
        chrom_name = chrom["chr"][3:]
        chrom_idx = CHROM_NAMES.index(chrom_name)
        for reo in chrom["reos"]:
            reo = reo["reo"]
            reo_pval = reo["log10pvalue"]
            reo_sig = reo["significant"]
            reo_effect = reo["score"]

            if reo_pval is None:
                continue

            if filter.numeric_intervals is not None:
                if reo_pval < filter.numeric_intervals.sig[0] or reo_pval > filter.numeric_intervals.sig[1]:
                    continue

                if reo_effect < filter.numeric_intervals.effect[0] or reo_effect > filter.numeric_intervals.effect[1]:
                    continue

            cat_filter = [
                EffectObservationDirectionType.ENRICHED.value in filter.categorical_facets
                and reo_sig
                and reo_effect > 0,
                EffectObservationDirectionType.DEPLETED.value in filter.categorical_facets
                and reo_sig
                and reo_effect < 0,
                EffectObservationDirectionType.NON_SIGNIFICANT.value in filter.categorical_facets and not reo_sig,
            ]

            if not any(cat_filter):
                continue

            bucket = buckets[((reo["source_start"] // BUCKET_SIZE) * BUCKET_SIZE) + 1]
            bucket.add_reo(reo, Bucket.ChromKey.GENE, filter.coverage_type)

        chroms[chrom_idx]["source_intervals"] = [
            {
                "start": loc,
                "count": b.count,
                "associated_buckets": gen_assoc_buckets(b),
                "log10_sig": b.log10_sig,
                "effect": b.effect,
            }
            for loc, b in buckets.items()
        ]

    for chrom in reos_genes:
        buckets = defaultdict(Bucket)
        chrom_name = chrom["chr"][3:]
        chrom_idx = CHROM_NAMES.index(chrom_name)
        for reo in chrom["reos"]:
            reo = reo["reo"]
            reo_pval = reo["log10pvalue"]
            reo_sig = reo["significant"]
            reo_effect = reo["score"]

            if reo_pval is None:
                continue

            if filter.numeric_intervals is not None:
                if reo_pval < filter.numeric_intervals.sig[0] or reo_pval > filter.numeric_intervals.sig[1]:
                    continue

                if reo_effect < filter.numeric_intervals.effect[0] or reo_effect > filter.numeric_intervals.effect[1]:
                    continue

            cat_filter = [
                EffectObservationDirectionType.ENRICHED.value in filter.categorical_facets
                and reo_sig
                and reo_effect > 0,
                EffectObservationDirectionType.DEPLETED.value in filter.categorical_facets
                and reo_sig
                and reo_effect < 0,
                EffectObservationDirectionType.NON_SIGNIFICANT.value in filter.categorical_facets and not reo_sig,
            ]

            if not any(cat_filter):
                continue

            bucket = buckets[((reo["gene_start"] // BUCKET_SIZE) * BUCKET_SIZE) + 1]
            bucket.add_reo(reo, Bucket.ChromKey.SOURCE, filter.coverage_type)

        chroms[chrom_idx]["target_intervals"] = [
            {
                "start": loc,
                "count": b.count,
                "associated_buckets": gen_assoc_buckets(b),
                "log10_sig": b.log10_sig,
                "effect": b.effect,
            }
            for loc, b in buckets.items()
        ]

    return chroms


def get_stats(igvf_value, filter):
    reos_sources = igvf_value["sources"]
    reos_genes = igvf_value["genes"]

    max_sig = float("-infinity")
    min_sig = float("infinity")
    max_effect = 0
    min_effect = float("infinity")

    reo_count = 0
    sources = set()
    genes = set()

    for chrom in reos_sources:
        for reo in chrom["reos"]:
            reo = reo["reo"]
            reo_pval = reo["log10pvalue"]
            reo_sig = reo["significant"]
            reo_effect = reo["score"]

            if reo_pval is None:
                continue

            if filter.numeric_intervals is not None:
                if reo_pval < filter.numeric_intervals.sig[0] or reo_pval > filter.numeric_intervals.sig[1]:
                    continue

                if reo_effect < filter.numeric_intervals.effect[0] or reo_effect > filter.numeric_intervals.effect[1]:
                    continue

            cat_filter = [
                EffectObservationDirectionType.ENRICHED.value in filter.categorical_facets
                and reo_sig
                and reo_effect > 0,
                EffectObservationDirectionType.DEPLETED.value in filter.categorical_facets
                and reo_sig
                and reo_effect < 0,
                EffectObservationDirectionType.NON_SIGNIFICANT.value in filter.categorical_facets and not reo_sig,
            ]

            if not any(cat_filter):
                continue

            reo_count += 1
            sources.add((reo["source_chr"], reo["source_start"], reo["source_end"]))
            genes.add((reo["gene_chr"], reo["gene_start"], reo["gene_end"]))
            try:
                max_sig = max(max_sig, reo_pval)
                min_sig = min(min_sig, reo_pval)
                max_effect = max(max_effect, reo_effect)
                min_effect = min(min_effect, reo_effect)
            except Exception as e:
                logger.error(reo)
                raise e

    for chrom in reos_genes:
        for reo in chrom["reos"]:
            reo = reo["reo"]
            reo_pval = reo["log10pvalue"]
            reo_sig = reo["significant"]
            reo_effect = reo["score"]

            if reo_pval is None:
                continue

            if filter.numeric_intervals is not None:
                if reo_pval < filter.numeric_intervals.sig[0] or reo_pval > filter.numeric_intervals.sig[1]:
                    continue

                if reo_effect < filter.numeric_intervals.effect[0] or reo_effect > filter.numeric_intervals.effect[1]:
                    continue

            cat_filter = [
                EffectObservationDirectionType.ENRICHED.value in filter.categorical_facets
                and reo_sig
                and reo_effect > 0,
                EffectObservationDirectionType.DEPLETED.value in filter.categorical_facets
                and reo_sig
                and reo_effect < 0,
                EffectObservationDirectionType.NON_SIGNIFICANT.value in filter.categorical_facets and not reo_sig,
            ]

            if not any(cat_filter):
                continue

            sources.add((reo["source_chr"], reo["source_start"], reo["source_end"]))
            genes.add((reo["gene_chr"], reo["gene_start"], reo["gene_end"]))
            try:
                max_sig = max(max_sig, reo_pval)
                min_sig = min(min_sig, reo_pval)
                max_effect = max(max_effect, reo_effect)
                min_effect = min(min_effect, reo_effect)
            except Exception as e:
                logger.error(reo)
                raise e

    return {
        "max_sig": max_sig,
        "min_sig": min_sig,
        "max_effect": max(max_effect, min_effect),
        "min_effect": min(max_effect, min_effect),
        "reo_count": reo_count,
        "source_count": len(sources),
        "target_count": len(genes),
    }


class CoverageView(View):
    def generate_data(self, data_filter):
        igvf_data = QueryCache.objects.all().order_by("-created_at").first()
        if igvf_data is None:
            update_coverage_data()
            return HttpResponseServerError("No IGVF Data found. Please try again in a few minutes.")

        if igvf_data.created_at < (datetime.now(timezone.utc) - timedelta(days=15)):
            update_coverage_data()

        stats = get_stats(igvf_data.value, data_filter)

        logger.debug(stats)
        coverage = {
            "chromosomes": gen_chroms(igvf_data.value, data_filter),
            "default_facets": default_facets(),
            "facets": view_facets(stats),
            "reo_count": stats["reo_count"],
            "source_count": stats["source_count"],
            "target_count": stats["target_count"],
        }
        return (coverage, stats)

    def get(self, request, *args, **kwargs):
        filter = Filter(
            chrom=None,
            categorical_facets=set(default_facets()),
            coverage_type=CoverageType.COUNT,
            numeric_intervals=FilterIntervals(
                effect=(float("-infinity"), float("infinity")), sig=(float("-infinity"), float("infinity"))
            ),
        )
        coverage, _ = self.generate_data(filter)
        return render(
            request,
            "coverage.html",
            {
                "coverage": coverage,
                "logged_in": not request.user.is_anonymous,
            },
        )

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
        except Exception as e:
            raise Http400(f"Invalid request body:\n{request.body}") from e

        if (zoom_chr := body.get("zoom")) is not None and zoom_chr not in CHROM_NAMES:
            raise Http400(f"Invalid chromosome in zoom: {zoom_chr}")
        coverage_type = body.get("coverage_type")

        try:
            body["filters"]
        except Exception as e:
            raise Http400(f'Invalid request body, no "filters" object:\n{request.body}') from e

        data_filter = get_filter(body["filters"], zoom_chr, coverage_type)
        coverage, stats = self.generate_data(data_filter)
        del coverage["default_facets"]
        del coverage["facets"]
        coverage["bucket_size"] = BUCKET_SIZE
        coverage["numeric_intervals"] = {
            "effect": (stats["min_effect"], stats["max_effect"]),
            "sig": (stats["min_sig"], stats["max_sig"]),
        }

        return JsonResponse(coverage)
