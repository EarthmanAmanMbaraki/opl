
from django.urls import path
from . views import (
    CustomerCreate,
    TruckCreate,
    CustomerExpandView, CustomerExpandMonthlyView, CustomerExpandDailyView,
    
)
app_name = "customer"
urlpatterns = [
    path('', CustomerCreate.as_view(), name="create_customer"),
    path('expand/', CustomerExpandView.as_view(), name="create_customer"),
    path('expand/monthly/', CustomerExpandMonthlyView.as_view(), name="customer_expand_monthly"),
    path('expand/daily/', CustomerExpandDailyView.as_view(), name="customer_expand_daily"),
    path('trucks/', TruckCreate.as_view(), name="create_truck"),
]
