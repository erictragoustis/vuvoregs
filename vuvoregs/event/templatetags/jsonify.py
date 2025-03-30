# In your event/templatetags/jsonify.py
from django import template
from django.core.serializers import serialize
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def jsonify(queryset):
    return mark_safe(serialize('json', queryset, use_natural_foreign_keys=True))