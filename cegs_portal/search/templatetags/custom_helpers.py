from django import template

register = template.Library()


@register.filter
def remove_underscores(value):
    return value.replace("_", " ")


@register.filter
def format_significance(significance):
    if significance < 0.000001:
        return "{:.2e}".format(significance)
    else:
        return "{:.6f}".format(significance)
