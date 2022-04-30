import datetime
from django.utils import timezone
from django.db.models.functions import ExtractMonth, ExtractYear
from django.db.models import Sum, F, FloatField, Count
from rest_framework.serializers import (
	ModelSerializer, 
	SerializerMethodField,
	ValidationError,	
	)

from order.models import Entry

from . models import Customer, Truck

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
YEARS = [2021, 2022]

def revenue(entries, quantity=False):
    if quantity:
        totals = [v for v in entries
                            .annotate(month=ExtractMonth('date'), year=ExtractYear('date'),)
                            .order_by()
                            .values('month', 'year')
                            .annotate(total=Sum("vol_obs"))
                            .values('month', 'year', 'total')
        ]
    else:
        totals = [v for v in entries
                                .annotate(month=ExtractMonth('date'), year=ExtractYear('date'),)
                                .order_by()
                                .values('month', 'year')
                                .annotate(total=Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                                .values('month', 'year', 'total')
            ]

    years = [] # List to hold records of years

    for year in YEARS:
        months = [] # Hold months
        filtered_totals = [total for total in totals if total['year'] == year]
        for month in filtered_totals:
            months.append({"month":MONTHS[month["month"]-1], "total":month["total"]})
        years.append({"year":year, "data":months})

    return years

def revenue_daily(entries, quantity=False):
    if quantity:
        totals = entries.values('date').order_by('date').annotate(sum=Sum("vol_obs"))
    else:
        totals = entries.values('date').order_by('date').annotate(sum=Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
    days = []
    for total in totals:
        timestamp = int(datetime.datetime.combine(total["date"], datetime.datetime.min.time()).timestamp())
        v = {
            "date": total["date"],
            "timestamp": timestamp,
            "sum": total["sum"]
        }

        days.append(v)
    
    return days

class CustomerCreateSer(ModelSerializer):
	
	class Meta:
		model = Customer
		fields = [
            "id",
			"depot",
			"name",
			"location",
		]

class CustomerExpandSer(ModelSerializer):
	revenue_monthly = SerializerMethodField()
	revenue_daily = SerializerMethodField()
	quantity_monthly = SerializerMethodField()
	quantity_daily = SerializerMethodField()

	class Meta:
		model = Customer
		fields = [
			"id",
			"name",
			"location",
			"revenue_monthly",
			"revenue_daily",
			"quantity_monthly",
			"quantity_daily"
		]	
	
	def get_revenue_monthly(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue(entries)
	
	def get_revenue_daily(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue_daily(entries)
	
	def get_quantity_monthly(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue(entries, True)
	
	def get_quantity_daily(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue_daily(entries, True)


class CustomerListSer(ModelSerializer):
	trucks = SerializerMethodField()
	class Meta:
		model = Customer
		fields = [
			"id",
			"name",
			"location",
			"trucks",
		]
	def get_trucks(self, obj):
		return TruckCreateSer(obj.truck_set.all(), many=True).data


class TruckCreateSer(ModelSerializer):
    
    class Meta:
        model = Truck
        fields = [
            "id",
			"customer",
			"plate_no",
            "driver"
		]
        


class TruckListSer(ModelSerializer):
    customer = SerializerMethodField()
    class Meta:
        model = Truck
        fields = [
            "id",
			"customer",
			"plate_no",
            "driver"
		]
        
    def get_customer(self, obj):
        return obj.customer.name

