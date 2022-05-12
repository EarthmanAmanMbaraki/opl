import datetime

from django.utils import timezone
from rest_framework.serializers import (
	ModelSerializer, 
	SerializerMethodField,
	ValidationError,	
	)
from customer.models import Customer
from django.db.models import Sum, F, FloatField, Count



from . models import Entry

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without truncateing'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))
    
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
    customer = SerializerMethodField()
    product = SerializerMethodField()
    depot = SerializerMethodField()
    truck = SerializerMethodField()
    product_id = SerializerMethodField()
    class Meta:
        model = Entry
        fields = [
            "id",
            "product",
            "product_id",
            "customer",
            "entry_no",
            "order_no",
            "date",
            "vol_obs",
            "vol_20",
            "selling_price",
            "depot",
            "truck",
        ]

    def get_product(self, obj):
        return obj.product.product.name
    def get_customer(self, obj):
        return obj.truck.customer.name
    def get_depot(self, obj):
        return obj.product.depot.name
    def get_truck(self, obj):
        return obj.truck.id
    def get_product_id(self, obj):
        return obj.product.id

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
            months_values.append(truncate(totals["sum"]/1000000, 2) if totals["sum"] != None else 0)
            orders.append(orders_totals["count"])
        data = {"name":obj.name, "values": months_values, "orders":orders}

        
        return {"months":MONTHS, "data": data}

