
from django.urls import path
from . views import (
    ProductList,
    DepotBI,
    ProductBI,
    UploadExcel,
    download,
    MainAPI,

    DepotListView,
    DepotExpandView,
    ProductListView,
    ProductExpandView,
    CustomerExpand,
    DepotListTimeSeriesView,
)
app_name = "depot"
urlpatterns = [
    path("", DepotListView.as_view(), name="depots"),
    path("expand/", DepotExpandView.as_view(), name="depots_entries"),
    path("products/", ProductListView.as_view(), name="products"),
    path("products/expand/", ProductExpandView.as_view(), name="products"),
    path("customers/expand/<int:pk>/", CustomerExpand.as_view(), name="customers_rank"),
    path("<int:pk>/", DepotListTimeSeriesView.as_view(), name="depots_time_series"),

    path('main/bi/<int:pk>/', MainAPI.as_view(), name="main_bi"),
    path('<int:depot_id>/products/', ProductList.as_view(), name="products_list"),
    path('bi/', DepotBI.as_view(), name="depot_bi"),

    path('<int:depot_id>/product_bi/', ProductBI.as_view(), name="product_bi"),
    path('<int:depot_id>/upload_excel/', UploadExcel.as_view(), name="upload_excel"),

    path('download/<int:depot_id>/', download, name="download"),
]
