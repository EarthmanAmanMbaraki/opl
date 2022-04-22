
from ast import If
from dataclasses import fields
import datetime
import quopri
from unicodedata import name
from django.contrib.auth.models import User
from django.db.models import Sum, F, FloatField, Count
from django.db.models.functions import ExtractMonth, ExtractYear
from rest_framework.serializers import (
	ModelSerializer,
    Serializer, 
	SerializerMethodField,
	ValidationError,	
	)

from customer.models import Customer
from order.models import Entry


from . models import Product, Depot
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
class ProductListSer(ModelSerializer):

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
        ]

class MainBISer(Serializer):
    revenue = SerializerMethodField()
    months = SerializerMethodField()
    class Meta:
        model = User
        fields = [
            "months",
            "revenue",
            
        ]
    
    def get_months(self, obj):
        products = list(set([prod.name for prod in Product.objects.all()]))
        values = []
        years = []
        available_dates = []
        for index, product in enumerate(products):
            

            totals = [v for v in Entry.objects.filter(product__name=product).annotate(month=ExtractMonth('date'), year=ExtractYear('date'),)
                            .order_by()
                            .values('month', 'year')
                            .annotate(total=Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                            .values('month', 'year', 'total')
            ]
            quantities = [v for v in Entry.objects.filter(product__name=product).annotate(month=ExtractMonth('date'), year=ExtractYear('date'),)
                            .order_by()
                            .values('month', 'year')
                            .annotate(total=Sum("vol_obs"))
                            .values('month', 'year', 'total')
            ]
            for total in totals:
                year = [idx for idx, item in enumerate(values) if item["year"] == total["year"]]
                print(year)
                if len(year) == 0:
                    year_ = total["year"]
                    
                    values.append({
                        "year":year_, 
                        "products":[]
                    })
                    year = [idx for idx, item in enumerate(values) if item["year"] == total["year"]]
                    
                    for p in products:
                        values[year[0]]["products"].append({
                            "name": p,
                            "values": [0] * 12,
                            "quantities": [0] * 12,
                        })
                    values[year[0]]["products"][index]["values"][total["month"]-1] = total["total"]
                else:
                    print(index)
                    print(values)
                    values[year[0]]["products"][index]["values"][total["month"]-1] = total["total"]

            for total in quantities:
                year = [idx for idx, item in enumerate(values) if item["year"] == total["year"]]
                values[year[0]]["products"][index]["quantities"][total["month"]-1] = total["total"]

        return values
    def get_revenue(self, obj):
        products = list(set([prod.name for prod in Product.objects.all()]))
        prod_values = []
       
        for product in products:
            data = {}
            data["name"] = product
            values = []
            quantity_value = []
            available_dates = []
            for depot in Depot.objects.all():
                prods = depot.product_set.filter(name=product)
                if prods.exists():
                    prod = prods.last()

                    totals = prod.entry_set.filter().values('date').order_by('date').annotate(sum=Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                    quantity_totals = prod.entry_set.filter().values('date').order_by('date').annotate(sum=Sum("vol_obs"))
                    dates = [total["date"] for total in totals]
                   

                    for index, date in enumerate(dates):
                        
                        timestamp = int(datetime.datetime.combine(date, datetime.datetime.min.time()).timestamp()) * 1000
                        
                
                        if date in available_dates:
                            for idx, value in enumerate(values): 
                                if value[0] == timestamp:
                                    values[idx][1] += round(totals[index]["sum"] / 1000000, 2)
                                    quantity_value[idx][1] += quantity_totals[index]["sum"]
                        else:
                            available_dates.append(date)
                            
                            values.append([timestamp, round(totals[index]["sum"] / 1000000, 2)])
                            quantity_value.append([timestamp, quantity_totals[index]["sum"]])
              
                        
                    data["dates"] = available_dates
                    data["values"] = values
                    data["quantities_values"] = quantity_value
       
            prod_values.append(data)
        return prod_values
                

class BISer(ModelSerializer):
    daily_products_comp = SerializerMethodField()
    months = SerializerMethodField()
    customers_month = SerializerMethodField()
    class Meta:
        model = Depot
        fields = [
            "id",
            "customers_month",
            "months",
            "daily_products_comp",
            
            
        ]

    def get_daily_products_comp(self, obj):
        products = []
        total_earns = 0
        total_orders = 0
        total_customers = len(list(set([customer.truck.customer.name for customer in Entry.objects.filter(product__depot=obj)])))
        for product in obj.product_set.all():
            # entries = product.entry_set.all().order_by("date")
            data = {}
            data["name"] = product.name
            totals = product.entry_set.filter().values('date').order_by('date').annotate(sum=Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
            orders_totals = product.entry_set.filter().values('date').order_by('date').annotate(count=Count("id"))
            available_dates = [total["date"] for total in totals]
            values = []
            orders = []
            total_earn = []
            total_order = []

            for index, date in enumerate(available_dates):
                try:
                    
                    values.append(round(totals[index]["sum"] / 1000000, 2))
                    orders.append(orders_totals[index]["count"])
                    total_earns += totals[index]["sum"]
                    total_orders += orders_totals[index]["count"]
                    total_earn.append(total_earns)
                    total_order.append(total_orders)
                except:
                    None

            data["dates"] = available_dates
            data["values"] = values
            data["totals"] = totals
            data["orders"] = orders
            data["total_orders"] = total_order
            data["total_earns"] = total_earn
            products.append(data)

        return {
            "dates": available_dates, "products":products, 
            "total_earns":total_earns, "total_orders":total_orders, "total_customers":total_customers,
        }
    
    def get_months(self, obj):
        products = []
        todays_date = datetime.date.today()
        for product in obj.product_set.all():
            months_values = []
            orders = []
            for month in range(1,13):
                
                totals = product.entry_set.filter(date__month=month).filter(date__year=todays_date.year).order_by('date').aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                orders_totals = product.entry_set.filter(date__month=month).order_by('date').aggregate(count =Count("id"))
                months_values.append(round(totals["sum"]/1000000, 2) if totals["sum"] != None else 0)
                orders.append(orders_totals["count"])
            data = {"name":product.name, "months": MONTHS, "values": months_values, "orders":orders}

            products.append(data)
        return {"months":MONTHS, "products": products}
    
    def get_customers_month(self, obj):
        customers = Customer.objects.all()
        month = datetime.date(2022, 2, 20).month
        
        customers_list = []

        for customer in customers:
            entries = Entry.objects.filter(truck__customer=customer)
            previous = 0
            if entries.exists():
                entries_sum = entries.filter(date__month=month).aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                
                if entries_sum["sum"] != None:
                    if month > 0:
                        previous_entries = entries.filter(date__month=month-1).aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                        if previous_entries["sum"] != None:
                            previous = previous_entries["sum"]
                    
                    customers_list.append({
                        "name":customer.name, 
                        "location": customer.location, 
                        "amount":entries_sum["sum"],
                        "increase": True if entries_sum["sum"] > previous else False
                    })
                    

                customers_list = sorted(customers_list, key=lambda d: d['amount'], reverse=True)[:8] 
        try:
            customers_list = customers_list[:8]
        except:
            None
        return customers_list


# PRODUCTS

class ProductBISer(ModelSerializer):
    main = SerializerMethodField()
    months = SerializerMethodField()
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "main",
            "months",
        ]
    def get_months(self, obj):
        months_values = []
        orders = []
        for month in range(1, 13):
            
            totals = obj.entry_set.filter(date__month=month).order_by('date').aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
            orders_totals = obj.entry_set.filter(date__month=month).order_by('date').aggregate(count =Count("id"))
            months_values.append(round(totals["sum"]/1000000, 2) if totals["sum"] != None else 0)
            orders.append(orders_totals["count"])
        data = {"name":obj.name, "values": months_values, "orders":orders}

        
        return {"months":MONTHS, "data": data}
    

    def get_main(self, obj):
        totals = obj.entry_set.filter().values('date').order_by('-date').annotate(sum=Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
        dates = []
        values = []
        for total in totals:
            date = int(datetime.datetime.combine(total["date"], datetime.datetime.min.time()).timestamp())
            value = round(total["sum"]/1000000, 2)
            dates.append(date*1000)
            values.append([date*1000, value])

        return {"dates": dates, "values":values, "total": totals}