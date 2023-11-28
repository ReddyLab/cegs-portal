from django.db import connection

from cegs_portal.search.models import DNAFeature


class FeatureIds:
    current_feature_id = None

    def __enter__(self):
        last_object = DNAFeature.objects.all().values_list("id", flat=True).order_by("-id")
        if len(last_object) > 0:
            self.current_feature_id = last_object[0]
        else:
            self.current_feature_id = 0
        return self

    def next_id(self):
        return self.__next__()

    def __iter__(self):
        return self

    def __next__(self):
        self.current_feature_id += 1
        return self.current_feature_id

    def __exit__(self, exc_type, exc_value, exc_tb):
        with connection.cursor() as cursor:
            cursor.execute("ALTER SEQUENCE search_dnafeature_id_seq RESTART WITH %s", (self.current_feature_id,))
