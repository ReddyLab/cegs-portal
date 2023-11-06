from django import template

register = template.Library()


@register.filter
def remove_underscores(value):
    return value.replace("_", " ")


@register.filter
def format_float(value):
    if abs(value) < 0.000001:
        return f"{value:.2e}"
    else:
        return f"{value:.6f}"


@register.filter
def if_strand(value):
    if value is not None:
        return value
    else:
        return "."
