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
from order.serializer import EntryListSer

from . models import Customer, Truck

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
YEARS = [2021, 2022]

def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without truncateing'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))

def revenue(entries, customer, quantity=False):
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

	years = [] # List to hold records of year
	for year in YEARS:
		months = [] # Hold months
		filtered_totals = [total for total in totals if total['year'] == year]
		total = 0
		orders_total = 0
		for month in filtered_totals:
			month_total = truncate(month["total"]/1000000, 2) if not quantity else month["total"]
			month_orders = len(entries.filter(date__month=month["month"]).filter(date__year=year))
			months.append({
				"month":month["month"]-1, 
				"total":month_total,
				"orders": month_orders,
			})
			total += month_total
			orders_total += month_orders
		years.append({
			"name": customer,
			"year":year, 
			"data":months, 
			"total":truncate(total, 2), 
			"orders":orders_total,
		})

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

class CustomerMinExpandSer(ModelSerializer):
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
			"quantity_daily",
			
		]	
		
	def get_revenue_monthly(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue(entries, obj.name)
	
	def get_revenue_daily(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue_daily(entries)
	
	def get_quantity_monthly(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue(entries, obj.name, True)
	
	def get_quantity_daily(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue_daily(entries, True)



class CustomerExpandMonthlySer(ModelSerializer):
	revenue_monthly = SerializerMethodField()
	quantity_monthly = SerializerMethodField()
	depot = SerializerMethodField()
	class Meta:
		model = Customer
		fields = [
			"id",
			"name",
			"depot",
			"location",
			"revenue_monthly",
			"quantity_monthly",
		]	
	
	def get_depot(self, obj):
		return obj.depot.name

	def get_revenue_monthly(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue(entries, obj.name)
	
	def get_quantity_monthly(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue(entries, obj.name, True)

class CustomerExpandDailySer(ModelSerializer):
	revenue_daily = SerializerMethodField()	
	quantity_daily = SerializerMethodField()
	class Meta:
		model = Customer
		fields = [
			"id",
			"name",
			"location",
			"revenue_daily",
			"quantity_daily",	
		]	
	
	def get_revenue_daily(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue_daily(entries)
	
	def get_quantity_daily(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue_daily(entries, True)


class CustomerExpandSer(ModelSerializer):
	revenue_monthly = SerializerMethodField()
	revenue_daily = SerializerMethodField()
	quantity_monthly = SerializerMethodField()
	quantity_daily = SerializerMethodField()
	entries = SerializerMethodField()
	class Meta:
		model = Customer
		fields = [
			"id",
			"name",
			"entries",
			"location",
			"revenue_monthly",
			"revenue_daily",
			"quantity_monthly",
			"quantity_daily",
			
		]	
	def get_entries(self, obj):
		return EntryListSer(Entry.objects.filter(truck__customer=obj), many=True).data

	def get_revenue_monthly(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue(entries, obj.name)
	
	def get_revenue_daily(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue_daily(entries)
	
	def get_quantity_monthly(self, obj):
		entries = Entry.objects.filter(truck__customer=obj)
		return revenue(entries, obj.name, True)
	
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

