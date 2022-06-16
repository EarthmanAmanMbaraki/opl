from django.contrib import admin
from django.urls import path, include
from main.views import FrontendAppView

handler404 = FrontendAppView.as_view()
handler500 = FrontendAppView.as_view()

admin.site.site_header = "OnePet Admin Site"
admin.site.site_title = "Admin"
admin.site.index_title = "Welcome to Admin Panel"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("customer/", include("customer.urls", namespace="customer")),
    path("depot/", include("depot.urls", namespace="depot")),
    path("", include("main.urls", namespace="main")),
    path("product/", include("product.urls", namespace="product")),
    path("sales/", include("sales.urls", namespace="sales")),
    path("silk/", include("silk.urls", namespace="silk")),
]
