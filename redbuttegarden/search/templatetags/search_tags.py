"""Expose plain-text result excerpts to search templates."""

from django import template

from search.excerpts import search_excerpt

register = template.Library()
register.filter("search_excerpt", search_excerpt)
