from django.contrib import admin
from .models import Tag, Recipe, Ingredient

admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(Recipe)
