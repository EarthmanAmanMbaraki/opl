from django.urls import path
from . views import (
    CreateEntry,
    UpdateEntry,
)

app_name = "order"
urlpatterns = [
    path('', CreateEntry.as_view(), name="create entry"),
    path('update/<int:pk>/', UpdateEntry.as_view(), name="update_entry"),
]
