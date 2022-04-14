from django.contrib import admin

# Local imports
from . models import (
    Entry,
)

admin.site.register(Entry)