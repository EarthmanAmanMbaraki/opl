from django.urls import path, re_path
from . views import (
    FrontendAppView,
)
app_name = "main"
urlpatterns = [
    re_path(r'^$', FrontendAppView.as_view(), name="frontend"),
]
