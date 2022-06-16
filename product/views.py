import datetime
from multiprocessing import context

from django.db.models import F
from django.core.cache import cache
from rest_framework.generics import (
    ListAPIView,
)
from rest_framework.response import Response
from rest_framework import status

from .models import Product
from .serializers import (
    RetrieveProductSer,
    ProductMonthSer,
    ProductSeriesSer,
    ProductTopCustomerMonthSer,
    ProductDepotMonthSer,
)


class ProductListView(ListAPIView):
    serializer_class = RetrieveProductSer
    queryset = Product.objects.all()

    def get(self, request, *args, **kwargs):
        e = cache.get("product", None)
        if not e:
            serializer = RetrieveProductSer(self.get_queryset(), many=True).data
            cache.set("product", serializer)
            return Response(serializer)
        return Response(e)


class ProductSeriesView(ListAPIView):
    serializer_class = ProductSeriesSer
    queryset = Product.objects.prefetch_related("sale_set").all()

    def get_serializer_context(self):
        start_date = self.request.GET.get("start_date", None)
        end_date = self.request.GET.get("end_date", None)
        if start_date and end_date:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        return {"start_date": start_date.date(), "end_date": end_date}

    def get(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        e = cache.get(
            "product-series-{}-{}".format(context["start_date"], context["end_date"]),
            None,
        )
        if not e:
            serializer = ProductSeriesSer(
                self.get_queryset(), many=True, context=context
            )
            cache.set(
                "product-series-{}-{}".format(
                    context["start_date"], context["end_date"]
                ),
                serializer.data,
            )
            return Response(serializer.data)
        return Response(e)


class ProductMonthView(ListAPIView):
    serializer_class = ProductMonthSer
    queryset = Product.objects.prefetch_related("sale_set").all()

    def get_serializer_context(self):
        year = self.request.GET.get("year", None)
        return {"year": year}

    def get(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        e = cache.get("product-month-{}".format(context["year"]), None)
        if not e:
            serializer = ProductMonthSer(
                self.get_queryset(), many=True, context=context
            )
            cache.set("product-month-{}".format(context["year"]), serializer.data)
            return Response(serializer.data)
        return Response(e)


class ProductDepotMonthView(ListAPIView):
    serializer_class = ProductDepotMonthSer
    queryset = Product.objects.prefetch_related("sale_set").all()

    def get_serializer_context(self):
        year = self.request.GET.get("year", None)
        return {"year": year}

    def get(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        e = cache.get("product-depot-month-{}".format(context["year"]))
        if not e:
            serializer = ProductDepotMonthSer(
                self.get_queryset(), many=True, context=context
            )
            cache.set("product-depot-month-{}".format(context["year"]), serializer.data)
            return Response(serializer.data)
        return Response(e)


class ProductTopCustomerMonthView(ListAPIView):
    serializer_class = ProductTopCustomerMonthSer
    queryset = Product.objects.prefetch_related("sale_set")

    def get_serializer_context(self):
        year = self.request.GET.get("year", None)
        month = self.request.GET.get("month", None)

        return {"year": year, "month": month}

    def get(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        e = cache.get(
            "product-top-customer-{}-{}".format(context["year"], context["month"]), None
        )
        if not e:
            serializer = ProductTopCustomerMonthSer(
                self.get_queryset(), many=True, context=context
            )
            cache.set(
                "product-top-customer-{}-{}".format(context["year"], context["month"]),
                serializer.data,
            )
            return Response(serializer.data)
        return Response(e)
