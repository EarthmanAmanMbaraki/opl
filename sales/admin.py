from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from sales.resources import SaleResource

from . models import Sale

class SaleAdmin(ImportExportModelAdmin):
    resource_class = SaleResource

admin.site.register(Sale, SaleAdmin)
