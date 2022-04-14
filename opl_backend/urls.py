
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Registering apps urls 
    
    path('accounts/', include("accounts.urls", namespace="accounts")),
    path('depots/', include("depot.urls", namespace="depots")),
    path('customers/', include("customer.urls", namespace="customers")),
    path('orders/', include("order.urls", namespace="orders")),
    path('', include("main.urls", namespace="main")),
]