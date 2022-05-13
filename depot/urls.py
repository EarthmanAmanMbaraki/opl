
from django.urls import path

from . views import (
    ProductList,
    UploadExcel,
    download,

    DepotListView,
    ProductListView,
    CustomerExpand,
    DepotListTimeSeriesView, DepotMonthlyView, DepotDailyView,
    DepotMainDailyView,DepotCustomerView,
    ProductMonthlyView, ProductDailyView,
    CustomerExpandAll, CustomerExpandMonth,
    DepotCustomersList,
)
app_name = "depot"
urlpatterns = [
    path("", DepotListView.as_view(), name="depots"),
    path("customers/", DepotCustomersList.as_view(), name="depots_customers"),
    path("expand/monthly/", DepotMonthlyView.as_view(), name="depot_monthly"),
    path("expand/daily/", DepotDailyView.as_view(), name="depot_daily"),
    path("expand/main/daily/", DepotMainDailyView.as_view(), name="depot_main_daily"),
    path("expand/customers/", DepotCustomerView.as_view(), name="depot_customers"),

    path("products/", ProductListView.as_view(), name="products"),
    path("products/expand/monthly/", ProductMonthlyView.as_view(), name="products_monthly"),
    path("products/expand/daily/", ProductDailyView.as_view(), name="products_daily"),
    
    path("customers/expand/<int:pk>/", CustomerExpand.as_view(), name="customers_rank"),
    path("customers/expand/<int:pk>/all/", CustomerExpandAll.as_view(), name="customers_expand_all"),
    path("customers/expand/<int:pk>/month/", CustomerExpandMonth.as_view(), name="customers_expand_month"),

    path("<int:pk>/", DepotListTimeSeriesView.as_view(), name="depots_time_series"),

    path('<int:depot_id>/products/', ProductList.as_view(), name="products_list"),

    path('<int:depot_id>/upload_excel/', UploadExcel.as_view(), name="upload_excel"),

    path('download/<int:depot_id>/', download, name="download"),
]
