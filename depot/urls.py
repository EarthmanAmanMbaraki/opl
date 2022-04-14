
from django.urls import path
from . views import (
    ProductList,
    DepotBI,
    ProductBI,
    UploadExcel,
    download,
)
app_name = "depot"
urlpatterns = [
    path('<int:depot_id>/products/', ProductList.as_view(), name="products"),
    path('<int:pk>/bi/', DepotBI.as_view(), name="depot_bi"),

    path('<int:depot_id>/product_bi/', ProductBI.as_view(), name="product_bi"),
    path('<int:depot_id>/upload_excel/', UploadExcel.as_view(), name="upload_excel"),

    path('download/', download, name="download"),
]
