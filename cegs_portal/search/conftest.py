from typing import Iterable, Optional

import pytest
from django.db.models import Manager, Model
from django.test import Client
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    Biosample,
    DNAFeature,
    DNAFeatureType,
    EffectObservationDirectionType,
    Experiment,
    ExperimentDataFileInfo,
    Facet,
    File,
    RegulatoryEffectObservation,
)
from cegs_portal.search.models.tests.dna_feature_factory import DNAFeatureFactory
from cegs_portal.search.models.tests.experiment_factory import (
    BiosampleFactory,
    ExperimentDataFileInfoFactory,
    ExperimentFactory,
)
from cegs_portal.search.models.tests.facet_factory import (
    FacetFactory,
    FacetValueFactory,
)
from cegs_portal.search.models.tests.file_factory import FileFactory
from cegs_portal.search.models.tests.reg_effects_factory import RegEffectFactory
from cegs_portal.users.conftest import group_extension  # noqa: F401
from cegs_portal.utils.pagination_types import MockPaginator, Pageable, Paginateable


class SearchClient:
    def __init__(
        self,
        user_model: Optional[Model] = None,
        group_model: Optional[Model] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        is_portal_admin: bool = False,
    ):
        self.client = Client()
        self.username = username
        self.password = password

        if user_model is not None and username is not None and password is not None:
            self.user = user_model.objects.create_user(username=username, password=password)
            self.user.is_portal_admin = is_portal_admin
            self.user.save()
            self.client.login(username=username, password=password)
        else:
            self.user = None

        if group_model is not None:
            assert user_model is not None
            self.group = group_model
            self.user.groups.add(group_model.group)
        else:
            self.group = None

    def get(self, *args, **kwargs):
        return self.client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.client.post(*args, **kwargs)

    def set_user_experiments(self, experiment_list: list[str]):
        if self.user is None:
            return

        self.user.experiments = experiment_list
        self.user.save()

    def set_group_experiments(self, experiment_list: list[str]):
        if self.group is None:
            return

        self.group.experiments = experiment_list
        self.group.save()


@pytest.fixture
def public_client():
    return SearchClient()


@pytest.fixture
def login_client(django_user_model):
    return SearchClient(user_model=django_user_model, username="user2", password="bar")


@pytest.fixture
def portal_admin_client(django_user_model):
    return SearchClient(user_model=django_user_model, username="user2", password="bar", is_portal_admin=True)


@pytest.fixture
def group_login_client(django_user_model, group_extension):  # # noqa: F811
    return SearchClient(user_model=django_user_model, group_model=group_extension, username="user3", password="bar")


@pytest.fixture
def experiment() -> Experiment:
    e = ExperimentFactory()
    _ = (_file(experiment=e), _file(experiment=e, data_file_info=data_file_info()))
    return e


@pytest.fixture
def private_experiment() -> Experiment:
    e = ExperimentFactory(public=False)
    _ = (_file(experiment=e), _file(experiment=e, data_file_info=data_file_info()))
    return e


@pytest.fixture
def archived_experiment() -> Experiment:
    e = ExperimentFactory(archived=True)
    _ = (_file(experiment=e), _file(experiment=e, data_file_info=data_file_info()))
    return e


@pytest.fixture
def access_control_experiments() -> tuple[Experiment, Experiment, Experiment]:
    e1 = ExperimentFactory()
    _ = (_file(experiment=e1), _file(experiment=e1, data_file_info=data_file_info()))
    e2 = ExperimentFactory(public=False)
    _ = (_file(experiment=e2), _file(experiment=e2, data_file_info=data_file_info()))
    e3 = ExperimentFactory(archived=True)
    _ = (_file(experiment=e3), _file(experiment=e3, data_file_info=data_file_info()))
    return (e1, e2, e3)


@pytest.fixture
def paged_experiments() -> Pageable[Experiment]:
    e1 = ExperimentFactory(biosamples=(BiosampleFactory(),))
    _ = (_file(experiment=e1), _file(experiment=e1, data_file_info=data_file_info()))
    e2 = ExperimentFactory(biosamples=(BiosampleFactory(),))
    _ = (_file(experiment=e2), _file(experiment=e2, data_file_info=data_file_info()))
    e3 = ExperimentFactory(biosamples=(BiosampleFactory(),))
    _ = (_file(experiment=e3), _file(experiment=e3, data_file_info=data_file_info()))
    e4 = ExperimentFactory(biosamples=(BiosampleFactory(),))
    _ = (_file(experiment=e4), _file(experiment=e4, data_file_info=data_file_info()))
    e5 = ExperimentFactory(biosamples=(BiosampleFactory(),))
    _ = (_file(experiment=e5), _file(experiment=e5, data_file_info=data_file_info()))
    e6 = ExperimentFactory(biosamples=(BiosampleFactory(),))
    _ = (_file(experiment=e6), _file(experiment=e6, data_file_info=data_file_info()))
    experiments = sorted([e1, e2, e3, e4, e5, e6], key=lambda x: x.accession_id)
    pages: Paginateable[Experiment] = MockPaginator(experiments, 3)
    return pages.page(1)


def data_file_info() -> ExperimentDataFileInfo:
    return ExperimentDataFileInfoFactory()


@pytest.fixture(name="data_file_info")
def dfi() -> ExperimentDataFileInfo:
    return data_file_info()


def _file(experiment=None, data_file_info=None) -> File:
    return FileFactory(experiment=experiment, data_file_info=data_file_info)


@pytest.fixture
def file() -> File:
    return _file()


@pytest.fixture
def biosample() -> Biosample:
    return BiosampleFactory()


@pytest.fixture
def feature_pages() -> Pageable[DNAFeature]:
    paginator: MockPaginator[DNAFeature] = MockPaginator(
        [
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
        ],
        3,
    )
    return paginator.page(2)


@pytest.fixture
def features() -> Iterable[DNAFeature]:
    f1 = DNAFeatureFactory(parent=None)
    f2 = DNAFeatureFactory(parent=None)
    f3 = DNAFeatureFactory(parent=None)
    f4 = DNAFeatureFactory(parent=None)
    f5 = DNAFeatureFactory(parent=None)
    return [f1, f2, f3, f4, f5]


@pytest.fixture
def feature() -> DNAFeature:
    return DNAFeatureFactory(parent=None)


@pytest.fixture
def search_feature() -> DNAFeature:
    return DNAFeatureFactory(parent=None, feature_type=DNAFeatureType.GENE)


@pytest.fixture
def private_feature() -> DNAFeature:
    return DNAFeatureFactory(parent=None, public=False)


@pytest.fixture
def archived_feature() -> DNAFeature:
    return DNAFeatureFactory(parent=None, archived=True)


@pytest.fixture
def nearby_feature_mix() -> tuple[DNAFeature, DNAFeature, DNAFeature]:
    pub_feature = DNAFeatureFactory(parent=None, feature_type=DNAFeatureType.GENE)
    private_feature = DNAFeatureFactory(
        parent=None,
        feature_type=DNAFeatureType.CCRE,
        chrom_name=pub_feature.chrom_name,
        location=NumericRange(pub_feature.location.lower + 1000, pub_feature.location.upper + 1000),
        public=False,
    )
    archived_feature = DNAFeatureFactory(
        parent=None,
        feature_type=DNAFeatureType.DHS,
        chrom_name=pub_feature.chrom_name,
        location=NumericRange(private_feature.location.lower + 1000, private_feature.location.upper + 1000),
        archived=True,
    )

    return (pub_feature, private_feature, archived_feature)


def _reg_effect(public=True, archived=False) -> RegulatoryEffectObservation:
    direction_facet = FacetFactory(description="", name=RegulatoryEffectObservation.Facet.DIRECTION.value)
    direction = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.ENRICHED)
    effect = RegEffectFactory(
        sources=(DNAFeatureFactory(parent=None), DNAFeatureFactory(parent=None)),
        facet_values=(direction,),
        public=public,
        archived=archived,
    )
    effect.experiment.biosamples.add(BiosampleFactory())
    effect.experiment.files.add(FileFactory(data_file_info=ExperimentDataFileInfoFactory()))
    return effect


@pytest.fixture
def reg_effect() -> RegulatoryEffectObservation:
    return _reg_effect()


@pytest.fixture
def private_reg_effect() -> RegulatoryEffectObservation:
    return _reg_effect(public=False)


@pytest.fixture
def archived_reg_effect() -> RegulatoryEffectObservation:
    return _reg_effect(archived=True)


@pytest.fixture
def source_reg_effects():
    source = DNAFeatureFactory(parent=None)

    reo1 = RegEffectFactory(
        sources=(source,),
    )
    reo2 = RegEffectFactory(
        sources=(source,),
    )
    reo3 = RegEffectFactory(
        sources=(source,),
    )
    return {
        "source": source,
        "effects": [reo1, reo2, reo3],
    }


@pytest.fixture
def hidden_source_reg_effects():
    source = DNAFeatureFactory(parent=None)

    reo1 = RegEffectFactory(
        sources=(source,),
        public=False,
    )
    reo2 = RegEffectFactory(
        sources=(source,),
        archived=True,
    )
    reo3 = RegEffectFactory(
        sources=(source,),
    )
    return {
        "source": source,
        "effects": [reo1, reo2, reo3],
    }


@pytest.fixture
def target_reg_effects():
    target = DNAFeatureFactory(parent=None)

    reo1 = RegEffectFactory(
        targets=(target,),
    )
    reo2 = RegEffectFactory(
        targets=(target,),
    )
    reo3 = RegEffectFactory(
        targets=(target,),
    )
    return {
        "target": target,
        "effects": [reo1, reo2, reo3],
    }


@pytest.fixture
def hidden_target_reg_effects():
    target = DNAFeatureFactory(parent=None)

    reo1 = RegEffectFactory(
        targets=(target,),
        public=False,
    )
    reo2 = RegEffectFactory(
        targets=(target,),
        archived=True,
    )
    reo3 = RegEffectFactory(
        targets=(target,),
    )
    return {
        "target": target,
        "effects": [reo1, reo2, reo3],
    }


@pytest.fixture
def facets() -> Manager[Facet]:
    f1 = FacetFactory()
    f2 = FacetFactory()
    _ = FacetValueFactory(facet=f1)
    _ = FacetValueFactory(facet=f1)
    _ = FacetValueFactory(facet=f2)
    _ = FacetValueFactory(facet=f2)
    return Facet.objects


@pytest.fixture
def paged_source_reg_effects() -> Pageable[RegulatoryEffectObservation]:
    source = DNAFeatureFactory(parent=None)

    paginator: MockPaginator[RegulatoryEffectObservation] = MockPaginator(
        [
            RegEffectFactory(
                sources=(source,),
            ),
            RegEffectFactory(
                sources=(source,),
            ),
            RegEffectFactory(
                sources=(source,),
            ),
            RegEffectFactory(
                sources=(source,),
            ),
            RegEffectFactory(
                sources=(source,),
            ),
            RegEffectFactory(
                sources=(source,),
            ),
        ],
        2,
    )
    return paginator.page(2)


@pytest.fixture
def genoverse_dhs_features():
    chrom = "chr10"
    start = 1_000_000
    length = 10_000
    gap = 1_000
    ref_genome = "GRCh38"
    f1 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start, start + length),
        feature_type=DNAFeatureType.DHS,
    )
    f2 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start + length + gap, start + length * 2 + gap),
        feature_type=DNAFeatureType.CCRE,
    )
    f3 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start + length * 2 + gap * 2, start + length * 3 + gap * 2),
        feature_type=DNAFeatureType.CCRE,
    )
    f4 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start + length * 3 + gap * 3, start + length * 4 + gap * 3),
        feature_type=DNAFeatureType.DHS,
    )
    f5 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start + length * 4 + gap * 4, start + length * 5 + gap * 4),
        feature_type=DNAFeatureType.DHS,
    )

    g1 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        feature_type=DNAFeatureType.GENE,
    )

    _ = RegEffectFactory(sources=(f1,), targets=(g1,))
    _ = RegEffectFactory(sources=(f2,))
    _ = RegEffectFactory(sources=(f3,))

    g1 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        feature_type=DNAFeatureType.GENE,
    )

    return {
        "chrom": chrom,
        "start": start,
        "end": start + length * 5 + gap * 4,
        "ref_genome": ref_genome,
        "features": [f1, f2, f3, f4, f5],
    }


@pytest.fixture
def genoverse_gene_features():
    chrom = "chr10"
    start = 1_000_000
    length = 10_000
    gap = 1_000
    ref_genome = "GRCh38"
    f1 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        strand="-",
        location=NumericRange(start, start + length),
        feature_type=DNAFeatureType.GENE,
    )
    f2 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        strand="-",
        location=NumericRange(start + length + gap, start + length * 2 + gap),
        feature_type=DNAFeatureType.GENE,
    )
    f3 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        strand="+",
        location=NumericRange(start + length * 2 + gap * 2, start + length * 3 + gap * 2),
        feature_type=DNAFeatureType.GENE,
    )
    f4 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        strand="+",
        location=NumericRange(start + length * 3 + gap * 3, start + length * 4 + gap * 3),
        feature_type=DNAFeatureType.GENE,
    )
    f5 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start + length * 4 + gap * 4, start + length * 5 + gap * 4),
        strand="-",
        feature_type=DNAFeatureType.GENE,
    )

    return {
        "chrom": chrom,
        "start": start,
        "end": start + length * 5 + gap * 4,
        "ref_genome": ref_genome,
        "features": [f1, f2, f3, f4, f5],
    }


@pytest.fixture
def genoverse_transcript_features():
    chrom = "chr10"
    start = 1_000_000
    end = 1_100_000
    ref_genome = "GRCh38"
    g1 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start, start + 40_000),
        strand="-",
        feature_type=DNAFeatureType.GENE,
    )

    g1_t1 = DNAFeatureFactory(
        parent=g1,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start, start + 40_000),
        strand="-",
        feature_type=DNAFeatureType.TRANSCRIPT,
    )

    g1_t1_e1 = DNAFeatureFactory(
        parent=g1_t1,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start, start + 10_000),
        strand="-",
        feature_type=DNAFeatureType.EXON,
    )
    g1_t1_e2 = DNAFeatureFactory(
        parent=g1_t1,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start + 20_000, start + 40_000),
        strand="-",
        feature_type=DNAFeatureType.EXON,
    )

    g2 = DNAFeatureFactory(
        parent=None,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start + 50_000, end),
        strand="+",
        feature_type=DNAFeatureType.GENE,
    )

    g2_t1 = DNAFeatureFactory(
        parent=g2,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start + 50_000, end),
        strand="+",
        feature_type=DNAFeatureType.TRANSCRIPT,
    )

    g2_t1_e1 = DNAFeatureFactory(
        parent=g2_t1,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start + 50_000, start + 70_000),
        strand="+",
        feature_type=DNAFeatureType.EXON,
    )
    g2_t1_e2 = DNAFeatureFactory(
        parent=g2_t1,
        ref_genome=ref_genome,
        chrom_name=chrom,
        location=NumericRange(start + 80_000, end),
        strand="+",
        feature_type=DNAFeatureType.EXON,
    )

    return {
        "chrom": chrom,
        "start": start,
        "end": end,
        "ref_genome": ref_genome,
        "features": [g1_t1, g1_t1_e1, g1_t1_e2, g2_t1, g2_t1_e1, g2_t1_e2],
    }
