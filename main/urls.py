from django.urls import path
from .views import (
    FrontendAppView,
)

app_name = "main"
urlpatterns = [
    path("", FrontendAppView.as_view(), name="frontend"),
]
