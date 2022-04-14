from django.urls import path
from . views import (
    CreateEntry,
    # excel_upload,
    CustomerBI,
    UpdateEntry,

)

app_name = "order"
urlpatterns = [
    path('', CreateEntry.as_view(), name="create entry"),
    path('update/<int:pk>/', UpdateEntry.as_view(), name="update_entry"),
    path('customer_bi/', CustomerBI.as_view(), name="customer_bi"),
    # path('upload/', excel_upload, name="excel_upload"),

]
