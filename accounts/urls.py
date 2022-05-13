from django.urls import path
from . views import (
    CustomAuthToken,
)

app_name = "accounts"

urlpatterns = [
     path('get-token/', CustomAuthToken.as_view(), name="get-token")
]
