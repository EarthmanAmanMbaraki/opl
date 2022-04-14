
from django.urls import path
from . views import (
    CustomerCreate,
    TruckCreate,
)
app_name = "customer"
urlpatterns = [
    path('', CustomerCreate.as_view(), name="create_customer"),
    path('trucks/', TruckCreate.as_view(), name="create_truck"),
]
