from django.contrib import admin
from . models import (
    Depot,
    DepotManager,
    Product,
)

admin.site.register(Depot)
admin.site.register(DepotManager)
admin.site.register(Product)
