from django.urls import path
from .views import (
    CreateSaleView,
    RetrieveSaleView,
    simple_upload,
    UploadExcel,
)

app_name = "sales"

urlpatterns = [
    path("", CreateSaleView.as_view(), name="sales"),
    path("<int:pk>/", RetrieveSaleView.as_view(), name="sales_retrieve"),
    path("<int:depot_id>/upload/", UploadExcel.as_view(), name="upload"),
]
