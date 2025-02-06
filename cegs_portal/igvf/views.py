import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Optional

from django.http import HttpResponseServerError, JsonResponse
from django.shortcuts import render
from django.views.generic import View

from cegs_portal.igvf.models import QueryCache, update_coverage_data
from cegs_portal.search.models import EffectObservationDirectionType
from cegs_portal.utils.http_exceptions import Http400

logger = logging.getLogger(__name__)


LARGE_BUCKET_SIZE = 2_000_000
SMALL_BUCKET_SIZE = 100_000
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
            "range": [stats.min_effect, stats.max_effect],
        },
        {
            "id": "Significance",
            "name": "Significance",
            "facet_type": "FacetType.NUMERIC",
            "description": "An adjusted p value",
            "coverage": ["Target", "Source"],
            "range64": [stats.min_sig, stats.max_sig],
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

    def add_reo(self, reo, comp_item, filter):
        self.count += 1

        match filter.coverage_type:
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
        bucket_size = SMALL_BUCKET_SIZE if filter.chrom is not None else LARGE_BUCKET_SIZE
        bucket = reo[f"{comp_item}_start"] // bucket_size
        self.associated_buckets.add((chrom_idx, bucket))


def chromosomes(chroms, filter):
    for chrom in chroms:
        chrom_name = chrom["chr"][3:]
        if filter.chrom is not None:
            if CHROM_NAMES[filter.chrom] != chrom_name:
                continue
            chrom_idx = 0
        else:
            chrom_idx = CHROM_NAMES.index(chrom_name)
        yield (chrom_idx, reos(chrom["reos"], filter))


def reos(reo_list, filter):
    for reo in reo_list:
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
            EffectObservationDirectionType.ENRICHED.value in filter.categorical_facets and reo_sig and reo_effect > 0,
            EffectObservationDirectionType.DEPLETED.value in filter.categorical_facets and reo_sig and reo_effect < 0,
            EffectObservationDirectionType.NON_SIGNIFICANT.value in filter.categorical_facets and not reo_sig,
        ]

        if not any(cat_filter):
            continue

        yield reo


class Chromosomes:
    class ReoTrack(StrEnum):
        Source = "source"
        Gene = "gene"

    def __init__(self, filter):
        self.bucket_size = SMALL_BUCKET_SIZE if filter.chrom is not None else LARGE_BUCKET_SIZE
        if filter.chrom is not None:
            self.chroms = [
                {
                    "chrom": CHROM_NAMES[filter.chrom],
                    "bucket_size": self.bucket_size,
                    "source_intervals": [],
                    "target_intervals": [],
                }
            ]
        else:
            self.chroms = [
                {"chrom": chrom, "bucket_size": self.bucket_size, "source_intervals": [], "target_intervals": []}
                for chrom in CHROM_NAMES
            ]

        self.source_buckets = defaultdict(lambda: defaultdict(Bucket))
        self.target_buckets = defaultdict(lambda: defaultdict(Bucket))
        self.filter = filter

    def gen_assoc_buckets(self, bucket):
        new_abs = []
        for ab in bucket.associated_buckets:
            new_abs.extend(ab)
        return new_abs

    def add_reo(self, chrom_idx, reo, track: ReoTrack):
        if track == Chromosomes.ReoTrack.Source:
            buckets = self.source_buckets[chrom_idx]
            comp_item = Bucket.ChromKey.GENE
        else:
            buckets = self.target_buckets[chrom_idx]
            comp_item = Bucket.ChromKey.SOURCE
        bucket = buckets[((reo[f"{track}_start"] // self.bucket_size) * self.bucket_size) + 1]
        bucket.add_reo(reo, comp_item, self.filter)

    def chrom_data(self):
        for i, chrom in enumerate(self.chroms):
            chrom["source_intervals"] = [
                {
                    "start": loc,
                    "count": b.count,
                    "associated_buckets": self.gen_assoc_buckets(b),
                    "log10_sig": b.log10_sig,
                    "effect": b.effect,
                }
                for loc, b in self.source_buckets[i].items()
            ]

            chrom["target_intervals"] = [
                {
                    "start": loc,
                    "count": b.count,
                    "associated_buckets": self.gen_assoc_buckets(b),
                    "log10_sig": b.log10_sig,
                    "effect": b.effect,
                }
                for loc, b in self.target_buckets[i].items()
            ]
        return self.chroms


class Stats:
    def __init__(self):
        self.max_sig = float("-infinity")
        self.min_sig = float("infinity")
        self.max_effect = 0
        self.min_effect = float("infinity")

        self.reo_count = 0
        self.sources = set()
        self.genes = set()

    def add_reo(self, reo, reo_value):
        reo_pval = reo["log10pvalue"]
        reo_effect = reo["score"]

        self.reo_count += reo_value
        self.sources.add((reo["source_chr"], reo["source_start"], reo["source_end"]))
        self.genes.add((reo["gene_chr"], reo["gene_start"], reo["gene_end"]))
        try:
            self.max_sig = max(self.max_sig, reo_pval)
            self.min_sig = min(self.min_sig, reo_pval)
            self.max_effect = max(self.max_effect, reo_effect)
            self.min_effect = min(self.min_effect, reo_effect)
        except Exception as e:
            logger.error(reo)
            raise e


class CoverageView(View):
    def generate_data(self, data_filter):
        igvf_data = QueryCache.objects.all().order_by("-created_at").first()
        if igvf_data is None:
            update_coverage_data()
            return HttpResponseServerError("No IGVF Data found. Please try again in a few minutes.")

        stats = Stats()
        chrom_data = Chromosomes(data_filter)
        for chrom_idx, reo_list in chromosomes(igvf_data.value["sources"], data_filter):
            for reo in reo_list:
                stats.add_reo(reo, 1)
                chrom_data.add_reo(chrom_idx, reo, Chromosomes.ReoTrack.Source)

        for chrom_idx, reo_list in chromosomes(igvf_data.value["genes"], data_filter):
            for reo in reo_list:
                stats.add_reo(reo, 0)
                chrom_data.add_reo(chrom_idx, reo, Chromosomes.ReoTrack.Gene)

        logger.debug(stats)
        return chrom_data.chrom_data(), stats

    def get(self, request, *args, **kwargs):
        filter = Filter(
            chrom=None,
            categorical_facets=set(default_facets()),
            coverage_type=CoverageType.COUNT,
            numeric_intervals=FilterIntervals(
                effect=(float("-infinity"), float("infinity")), sig=(float("-infinity"), float("infinity"))
            ),
        )
        chrom_data, stats = self.generate_data(filter)
        return render(
            request,
            "coverage.html",
            {
                "coverage": {
                    "chromosomes": chrom_data,
                    "default_facets": default_facets(),
                    "facets": view_facets(stats),
                    "reo_count": stats.reo_count,
                    "source_count": len(stats.sources),
                    "target_count": len(stats.genes),
                },
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
        chrom_data, stats = self.generate_data(data_filter)

        return JsonResponse(
            {
                "chromosomes": chrom_data,
                "bucket_size": SMALL_BUCKET_SIZE if data_filter.chrom is not None else LARGE_BUCKET_SIZE,
                "numeric_intervals": {
                    "effect": (stats.min_effect, stats.max_effect),
                    "sig": (stats.min_sig, stats.max_sig),
                },
                "reo_count": stats.reo_count,
                "source_count": len(stats.sources),
                "target_count": len(stats.genes),
            }
        )
