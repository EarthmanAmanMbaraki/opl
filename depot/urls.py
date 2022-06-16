from django.urls import path
from .views import (
    DepotListView,
    DepotMonthView,
    DepotProductMonthView,
    DepotSeriesView,
    DepotProductSeriesView,
    DepotCustomerMonthView,
    download,
)

app_name = "depot"

urlpatterns = [
    path("", DepotListView.as_view(), name="depot"),
    path("month/", DepotMonthView.as_view(), name="month"),
    path("product/month/", DepotProductMonthView.as_view(), name="product_month"),
    path("series/<int:pk>/", DepotSeriesView.as_view(), name="depot_series"),
    path(
        "product/series/<int:pk>/",
        DepotProductSeriesView.as_view(),
        name="product_series",
    ),
    path("customer/<int:pk>/", DepotCustomerMonthView.as_view(), name="depot_customer"),
    path("download/<int:depot_id>/", download, name="download_template"),
]
