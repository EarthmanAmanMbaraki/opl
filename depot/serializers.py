
from ast import If
import datetime
from django.db.models import Sum, F, FloatField, Count
from rest_framework.serializers import (
	ModelSerializer, 
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
        DAYS = 7
        products = []
        base = datetime.date(2022, 1, 23)
        date_list = [base - datetime.timedelta(days=x) for x in range(DAYS)]
        date_list = sorted(date_list)
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
            values = [0] * DAYS
            orders = [0] * DAYS
            total_earn = [0] * DAYS
            total_order = [0] * DAYS
            for index, date in enumerate(available_dates):
                try:
                    idx = date_list.index(date)
                    values[idx] = round(totals[index]["sum"] / 1000000, 2)
                    orders[idx] = orders_totals[index]["count"]
                    total_earns += totals[index]["sum"]
                    total_orders += orders_totals[index]["count"]
                    total_earn[idx] = total_earns
                    total_order[idx] = total_orders
                except:
                    None

            data["dates"] = date_list
            data["values"] = values
            data["totals"] = totals
            data["orders"] = orders
            data["total_orders"] = total_order
            data["total_earns"] = total_earn
            products.append(data)

        return {
            "dates": date_list, "products":products, 
            "total_earns":total_earns, "total_orders":total_orders, "total_customers":total_customers,
        }
    
    def get_months(self, obj):
        products = []
        
        for product in obj.product_set.all():
            months_values = []
            orders = []
            for month in range(1,13):
                
                totals = product.entry_set.filter(date__month=month).order_by('date').aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
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