from datetime import datetime, timezone

from django.db import models

from cegs_portal.search.models.utils import AccessionId, AccessionType
from cegs_portal.search.models.validators import validate_accession_id


class Accessioned(models.Model):
    class Meta:
        abstract = True

    class Facets:
        pass

    accession_id = models.CharField(max_length=15, validators=[validate_accession_id], unique=True)


class AccessionIdLog(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["accession_type"], name="sal_type_index"),
            models.Index(fields=["created_at"], name="sal_created_index"),
        ]

    ACCESSION_TYPE = [
        (str(AccessionType.GENE), AccessionType.GENE.value),
        (str(AccessionType.TRANSCRIPT), AccessionType.TRANSCRIPT.value),
        (str(AccessionType.EXON), AccessionType.EXON.value),
        (str(AccessionType.REGULATORY_EFFECT_OBS), AccessionType.REGULATORY_EFFECT_OBS.value),
        (str(AccessionType.GRNA), AccessionType.GRNA.value),
        (str(AccessionType.CCRE), AccessionType.CCRE.value),
        (str(AccessionType.DHS), AccessionType.DHS.value),
        (str(AccessionType.EXPERIMENT), AccessionType.EXPERIMENT.value),
        (str(AccessionType.CAR), AccessionType.CAR.value),
        (str(AccessionType.TT), AccessionType.TT.value),
        (str(AccessionType.CL), AccessionType.CL.value),
        (str(AccessionType.BIOS), AccessionType.BIOS.value),
    ]
    created_at = models.DateTimeField()
    accession_type = models.CharField(max_length=100, choices=ACCESSION_TYPE)
    accession_id = models.CharField(max_length=15, validators=[validate_accession_id], unique=True)
    message = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.created_at} {self.accession_id}: {self.message}"

    @classmethod
    def latest(cls, atype: AccessionType):
        return AccessionIdLog.objects.filter(accession_type=atype).order_by("-created_at").first()


class AccessionIds:
    def __init__(self, message: str = ""):
        self.id_dict: dict[AccessionType, AccessionId] = {}
        self.modified_dict: dict[AccessionType, bool] = {}
        self.message = message

    def _load(self, atype: AccessionType):
        if atype in self.id_dict:
            return self.id_dict[atype]

        entry = AccessionIdLog.latest(atype)
        if entry is not None:
            result = AccessionId(entry.accession_id)
        else:
            result = AccessionId.start_id(atype)
        self.id_dict[atype] = result
        self.modified_dict[atype] = False
        return result

    def incr(self, key: AccessionType):
        old_value = str(self._load(key))
        self.id_dict[key].incr()
        self.modified_dict[key] = True
        return old_value

    def __setitem__(self, key: AccessionType, accession_id: AccessionId):
        self.id_dict[key] = accession_id

    def __getitem__(self, key: AccessionType):
        return self._load(key)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        now = datetime.now(timezone.utc)
        log_items = []
        for (atype, accession_id) in self.id_dict.items():
            if self.modified_dict[atype]:
                log_items.append(
                    AccessionIdLog(
                        created_at=now, accession_type=str(atype), accession_id=str(accession_id), message=self.message
                    )
                )
        AccessionIdLog.objects.bulk_create(log_items)
