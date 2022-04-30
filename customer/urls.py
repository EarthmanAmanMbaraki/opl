
from django.urls import path
from . views import (
    CustomerCreate,
    TruckCreate,
    CustomerExpandView,
)
app_name = "customer"
urlpatterns = [
    path('', CustomerCreate.as_view(), name="create_customer"),
    path('expand/', CustomerExpandView.as_view(), name="create_customer"),
    path('trucks/', TruckCreate.as_view(), name="create_truck"),
]
