from django.contrib import admin
from . models import (
    Depot,  
    DepotManager,   
)

admin.site.register(Depot)
admin.site.register(DepotManager)