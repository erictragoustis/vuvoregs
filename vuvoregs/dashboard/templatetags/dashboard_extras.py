from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def flatten_value(value):
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return value


@register.filter
def attr(obj, attr_name):
    return getattr(obj, attr_name, None)