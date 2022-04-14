from django.contrib import admin

from . models import (
    Customer,
    Truck,
)

admin.site.register(Customer)
admin.site.register(Truck)
