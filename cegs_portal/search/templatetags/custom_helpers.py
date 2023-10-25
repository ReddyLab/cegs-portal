from django import template

register = template.Library()


@register.filter
def remove_underscores(value):
    return value.replace("_", " ")


@register.filter
def format_float(significance):
    if significance < 0.000001:
        return f"{significance:.2e}"
    else:
        return f"{significance:.6f}"
