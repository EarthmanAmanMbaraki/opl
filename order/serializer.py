import datetime

from django.utils import timezone
from rest_framework.serializers import (
	ModelSerializer, 
	SerializerMethodField,
	ValidationError,	
	)
from customer.models import Customer
from django.db.models import Sum, F, FloatField, Count
from customer.serializers import TruckListSer
from depot.serializers import ProductListSer

from . models import Entry

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

class EntryCreateSer(ModelSerializer):

    class Meta:
        model = Entry
        fields = [
            "id",
            "product",
            "truck",
            "entry_no",
            "order_no",
            "date",
            "vol_obs",
            "vol_20",
            "selling_price",
        ]

class EntryListSer(ModelSerializer):
    product = SerializerMethodField()
    truck = SerializerMethodField()

    class Meta:
        model = Entry
        fields = [
            "id",
            "product",
            "truck",
            "entry_no",
            "order_no",
            "date",
            "vol_obs",
            "vol_20",
            "selling_price",
        ]

    def get_product(self, obj):
        return ProductListSer(obj.product).data

    def get_truck(self, obj):
        return TruckListSer(obj.truck).data


class CustomerBISer(ModelSerializer):
    orders = SerializerMethodField()
    monthly_orders = SerializerMethodField()
    order_total = SerializerMethodField()
    total = SerializerMethodField()
    truck_total = SerializerMethodField()
    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "order_total",
            "location",
            "total",
            "truck_total",
            "orders",
            "monthly_orders",
        ]

    def get_orders(self, obj):
        return EntryListSer(Entry.objects.filter(truck__customer=obj), many=True).data
    
    def get_order_total(self, obj):
        return len(Entry.objects.filter(truck__customer=obj))

    def get_total(self, obj):
        entries = Entry.objects.filter(truck__customer=obj).aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
        return entries["sum"]

    def get_truck_total(self, obj):
        return len(obj.truck_set.all())

    def get_monthly_orders(self, obj):
        months_values = []
        orders = []
        for month in range(1, 13):
            entries = Entry.objects.filter(truck__customer=obj)
            totals = entries.filter(date__month=month).order_by('date').aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
            orders_totals = entries.filter(date__month=month).order_by('date').aggregate(count =Count("id"))
            months_values.append(round(totals["sum"]/1000000, 2) if totals["sum"] != None else 0)
            orders.append(orders_totals["count"])
        data = {"name":obj.name, "values": months_values, "orders":orders}

        
        return {"months":MONTHS, "data": data}

