import csv

from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNAFeature, Facet, FacetValue
from cegs_portal.search.models.dna_feature import DNAFeatureType
from utils import timer

CCRE_FACET = Facet.objects.get(name="cCRE Category")
CCRE_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=CCRE_FACET.id).all()}

OVERLAP_FACET = Facet.objects.get(name="cCRE Overlap")
OVERLAP_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=OVERLAP_FACET.id).all()}


@timer("Add cCRE Categories to DHSs")
def run(closest_filename):
    with open(closest_filename) as closest_file:
        reader = csv.reader(closest_file, delimiter="\t")
        current_chr = None
        current_start = None
        current_end = None
        current_dhs = None
        current_ccre_locations = set()
        for row in reader:
            dhs_chr, dhs_start, dhs_end = row[0], int(row[1]), int(row[2]) + 1
            ccre_start, ccre_end = int(row[4]), int(row[5]) + 1

            if current_dhs is None:
                current_dhs = DNAFeature.objects.get(
                    chrom_name=dhs_chr, location=NumericRange(dhs_start, dhs_end), feature_type=DNAFeatureType.DHS
                )
                current_chr, current_start, current_end = dhs_chr, dhs_start, dhs_end

            assert current_dhs is not None

            if current_chr == dhs_chr and current_start == dhs_start and current_end == dhs_end:
                # make sure the closest ccre actually overlaps
                if (
                    (ccre_end > dhs_start and ccre_end <= dhs_end)
                    or (ccre_start >= dhs_start and ccre_start < dhs_end)
                    or (ccre_start <= dhs_start and ccre_end >= dhs_end)
                ):
                    current_ccre_locations.add(NumericRange(ccre_start, ccre_end))
            else:
                if len(current_ccre_locations) == 0:
                    overlap_facet = OVERLAP_FACET_VALUES["No overlaps"]
                elif len(current_ccre_locations) == 1:
                    overlap_facet = OVERLAP_FACET_VALUES["One overlap"]
                else:
                    overlap_facet = OVERLAP_FACET_VALUES["Multiple overlaps"]

                current_ccres = DNAFeature.objects.filter(
                    chrom_name=current_chr, location__in=list(current_ccre_locations), feature_type=DNAFeatureType.CCRE
                ).prefetch_related("facet_values")
                ccre_category_set = set()
                for ccre in current_ccres.all():
                    for value in ccre.facet_values.all():
                        if value.facet_id == CCRE_FACET.id:
                            ccre_category_set.add(value)

                # Data sanity checks
                # if CCRE_FACET_VALUES["pELS"] in ccre_category_set and CCRE_FACET_VALUES["dELS"] in ccre_category_set:
                #     print(
                #     f"pELS and dELS for {current_chr}: {current_start}-{current_end} ({current_end - current_start})"
                #     )
                #     for ccre in current_ccres.all():
                #         print(f"{ccre}: {[v.value for v in ccre.facet_values.all()]}")

                # if CCRE_FACET_VALUES["PLS"] in ccre_category_set and CCRE_FACET_VALUES["pELS"] in ccre_category_set:
                #     print(
                #     f"PLS and pELS for {current_chr}: {current_start}-{current_end} ({current_end - current_start})"
                #     )
                #     for ccre in current_ccres.all():
                #         print(f"{ccre}: {[v.value for v in ccre.facet_values.all()]}")

                # if CCRE_FACET_VALUES["PLS"] in ccre_category_set and CCRE_FACET_VALUES["dELS"] in ccre_category_set:
                #     print(
                #     f"PLS and dELS for {current_chr}: {current_start}-{current_end} ({current_end - current_start})"
                #     )
                #     for ccre in current_ccres.all():
                #         print(f"{ccre}: {[v.value for v in ccre.facet_values.all()]}")

                # assert not (
                #     CCRE_FACET_VALUES["pELS"] in ccre_category_set and CCRE_FACET_VALUES["dELS"] in ccre_category_set
                # )
                # assert not (
                #     CCRE_FACET_VALUES["PLS"] in ccre_category_set and CCRE_FACET_VALUES["pELS"] in ccre_category_set
                # )
                # assert not (
                #     CCRE_FACET_VALUES["PLS"] in ccre_category_set and CCRE_FACET_VALUES["dELS"] in ccre_category_set
                # )

                # All ccre locations should exist in the database.
                if len(ccre_category_set) == 0 and len(current_ccre_locations) != 0:
                    print(f"These ccres should exist but don't: {current_chr}: {current_ccre_locations}")

                current_dhs.facet_values.add(overlap_facet)
                current_dhs.facet_values.add(*list(ccre_category_set))

                current_chr, current_start, current_end = dhs_chr, dhs_start, dhs_end
                current_dhs = DNAFeature.objects.get(
                    chrom_name=current_chr,
                    location=NumericRange(current_start, current_end),
                    feature_type=DNAFeatureType.DHS,
                )
                assert current_dhs is not None
                current_ccre_locations = set()

                if (
                    (ccre_end > dhs_start and ccre_end <= dhs_end)
                    or (ccre_start >= dhs_start and ccre_start < dhs_end)
                    or (ccre_start <= dhs_start and ccre_end >= dhs_end)
                ):
                    current_ccre_locations.add(NumericRange(ccre_start, ccre_end))

        if len(current_ccre_locations) == 0:
            overlap_facet = OVERLAP_FACET_VALUES["No overlaps"]
        elif len(current_ccre_locations) == 1:
            overlap_facet = OVERLAP_FACET_VALUES["One overlap"]
        else:
            overlap_facet = OVERLAP_FACET_VALUES["Multiple overlaps"]

        current_ccres = DNAFeature.objects.filter(
            chrom_name=current_chr, location__in=list(current_ccre_locations), feature_type=DNAFeatureType.CCRE
        ).prefetch_related("facet_values")
        ccre_category_set = set()
        for ccre in current_ccres.all():
            for value in ccre.facet_values.all():
                if value.facet_id == CCRE_FACET.id:
                    ccre_category_set.add(value)

        # All ccre locations should exist in the database.
        if len(ccre_category_set) == 0 and len(current_ccre_locations) != 0:
            print(f"These ccres should exist but don't: {current_chr}: {current_ccre_locations}")

        current_dhs.facet_values.add(overlap_facet)
        current_dhs.facet_values.add(*list(ccre_category_set))
