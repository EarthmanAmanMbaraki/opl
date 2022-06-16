from django.urls import path
from .views import (
    ProductListView,
    ProductSeriesView,
    ProductMonthView,
    ProductTopCustomerMonthView,
    ProductDepotMonthView,
)

app_name = "product"

urlpatterns = [
    path("", ProductListView.as_view(), name="product"),
    path("series/", ProductSeriesView.as_view(), name="series"),
    path("month/", ProductMonthView.as_view(), name="month"),
    path("depot/month/", ProductDepotMonthView.as_view(), name="product_depot_month"),
    path("customer/top/", ProductTopCustomerMonthView.as_view(), name="customer_top"),
]
