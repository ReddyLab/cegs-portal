from django import template

register = template.Library()


@register.filter
def is_bed6(options):
    return options is not None and options.get("tsv_format", None) == "bed6"
