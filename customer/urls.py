from django.urls import path
from .views import (
    # Customer Views
    CreateCustomerView,
    TopCustomerMonthView,
    CustomerDetailView,
    # Driver Views
    CreateDriverView,
    # Truck Views
    CreateTruckView,
    AddCustomer,
    CreateC,
)

app_name = "customer"

urlpatterns = [
    # Customer urls
    path("", CreateCustomerView.as_view(), name="customer"),
    path("<int:pk>/", CustomerDetailView.as_view(), name="customer_detail"),
    path(
        "top/month/<int:pk>/", TopCustomerMonthView.as_view(), name="top_customer_month"
    ),
    # Driver urls
    path("drivers/", CreateDriverView.as_view(), name="drivers"),
    # Truck urls
    path("trucks/", CreateTruckView.as_view(), name="trucks"),
    path("add/", AddCustomer.as_view(), name="add"),
    path("test/", CreateC.as_view(), name="test"),
]
