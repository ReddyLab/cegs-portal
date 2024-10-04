from typing import Optional


def get_or_create_facet(Facet, facet_name, description, facet_type):
    facet = Facet.objects.filter(name=facet_name).first()
    if facet is None:
        facet = Facet(name=facet_name, description=description, facet_type=facet_type)
        facet.save()
    return facet


def get_or_create_facet_value(FacetValue, facet_value, facet):
    fv = FacetValue.objects.filter(value=facet_value).first()
    if fv is None:
        fv = FacetValue(value=facet_value, facet=facet)
        fv.save()

    return fv


def delete_facet_value(FacetValue, facet_value):
    fv = FacetValue.objects.filter(value=facet_value).first()
    if fv is not None:
        fv.delete()


def change_facet(
    Facet, old_facet_name: str, new_facet_name: Optional[str] = None, new_facet_description: Optional[str] = None
):
    facet = Facet.objects.get(name=old_facet_name)
    if new_facet_name is not None:
        facet.name = new_facet_name

    if new_facet_description is not None:
        facet.description = new_facet_description

    facet.save()
