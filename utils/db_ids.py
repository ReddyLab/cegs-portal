from django.db import connection

from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation


class FeatureIds:
    # Only one "FeatureIds" should be in use at a time. Otherwise
    # the FeatureIds instances will potentially assign the same ids
    # to different rows, and one of the commits will fail.
    in_use = False

    def __init__(self):
        self.current_id = None

    def __enter__(self):
        assert FeatureIds.in_use is False
        FeatureIds.in_use = True

        last_object = DNAFeature.objects.all().values_list("id", flat=True).order_by("-id")
        if last_object.exists():
            self.current_id = last_object[0]
        else:
            self.current_id = 0
        return self

    def next_id(self):
        return self.__next__()

    def __iter__(self):
        return self

    def __next__(self):
        self.current_id += 1
        return self.current_id

    def __exit__(self, exc_type, exc_value, exc_tb):
        FeatureIds.in_use = False
        with connection.cursor() as cursor:
            cursor.execute("ALTER SEQUENCE search_dnafeature_id_seq RESTART WITH %s", (self.current_id,))


class ReoIds:
    # Only one "FeatureIds" should be in use at a time. Otherwise
    # the FeatureIds instances will potentially assign the same ids
    # to different rows, and one of the commits will fail.
    in_use = False

    def __init__(self):
        self.current_id = None

    def __enter__(self):
        assert ReoIds.in_use is False
        ReoIds.in_use = True

        last_object = RegulatoryEffectObservation.objects.all().values_list("id", flat=True).order_by("-id")
        if last_object.exists():
            self.current_id = last_object[0]
        else:
            self.current_id = 0
        return self

    def next_id(self):
        return self.__next__()

    def __iter__(self):
        return self

    def __next__(self):
        self.current_id += 1
        return self.current_id

    def __exit__(self, exc_type, exc_value, exc_tb):
        ReoIds.in_use = False
        with connection.cursor() as cursor:
            cursor.execute("ALTER SEQUENCE search_regulatoryeffect_id_seq RESTART WITH %s", (self.current_id,))
