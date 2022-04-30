from calendar import month
import datetime
from pyexpat import model
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
from customer.serializers import CustomerExpandSer
from order.models import Entry
from order.serializer import EntryCreateSer


from . models import DepotProduct, Product, Depot
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
YEARS = [2022, 2021]

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
            months.append({"month":month["month"], "total":month["total"] if quantity else round(month['total']/1000000, 2)})
        years.append({"year":year, "months":MONTHS, "data":months})

    return years

def revenue_daily(entries, quantity=False):
    if quantity:
        totals = entries.values('date').order_by('date').annotate(sum=Sum("vol_obs"))
    else:
        totals = entries.values('date').order_by('date').annotate(sum=Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
    days = []
    for total in totals:
        timestamp = int(datetime.datetime.combine(total["date"], datetime.datetime.min.time()).timestamp()) * 1000
        v = {
            "date": total["date"],
            "timestamp": timestamp,
            "sum":  total["sum"] if quantity == True else round(total["sum"]/1000000, 2)
        }

        days.append(v)
    
    return days

def customer_ranks(years):
    customers = Customer.objects.all()
        
    customers_list = []

    for customer in customers:
        entries = Entry.objects.filter(truck__customer=customer)

        if entries.exists():
            entries_sum = entries.aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
            
            if entries_sum["sum"] != None:
                
                
                customers_list.append({
                    "name":customer.name, 
                    "location": customer.location, 
                    "amount":entries_sum["sum"],
                })
                

            customers_list = sorted(customers_list, key=lambda d: d['amount'], reverse=True)

    return customers_list

def customer_total(year, month):
    c = []
    for customer in Customer.objects.all():
        entries = Entry.objects.filter(truck__customer=customer)
        if entries.exists():
            entries_sum = entries.filter(date__year=year).filter(date__month=month+1).aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
            if entries_sum["sum"] != None:
                c.append({
                    "name":customer.name, 
                    "location": customer.location, 
                    "amount":entries_sum["sum"],
                })
    c = sorted(c, key=lambda d: d['amount'], reverse=True)
    return c

def depot_totals(entries, quantity=False):
    if quantity:
        total = sum([entry.vol_obs for entry in entries])
    else:
        total = sum([(entry.vol_obs * float(entry.selling_price)) for entry in entries])
        total = round(total/1000000, 2)
    return total

class DepotListTimeSeriesSer(ModelSerializer):
    years_revenue = SerializerMethodField()
    years_quantity = SerializerMethodField()
    months_revenue = SerializerMethodField()
    months_quantity = SerializerMethodField()
    depots = SerializerMethodField()
    class Meta:
        model = User
        fields = [
            "depots",
            "years_revenue",
            "years_quantity",
            "months_revenue",
            "months_quantity",
            
        ]
    
    def get_depots(self, obj):
        return [depot.name for depot in Depot.objects.all()]

    def get_months_revenue(self, obj):
        years = []
        for year in YEARS:
            months_values = []
            for month in range(1, 13):
                for product in Product.objects.all():
                    depot_values = []    
                    for depot in Depot.objects.all():
                        entries = Entry.objects.filter(date__year=year).filter(date__month=month).filter(product__product=product).filter(product__depot=depot)
                        depot_values.append(depot_totals(entries))
                    months_values.append({"name":product.name, "month":month, "values":depot_values})
                    
            years.append({"year":year, "values":months_values})
            
        return years
    
    def get_months_quantity(self, obj):
        years = []
        for year in YEARS:
            months_values = []
            for month in range(1, 13):
                for product in Product.objects.all():
                    depot_values = []    
                    for depot in Depot.objects.all():
                        entries = Entry.objects.filter(date__year=year).filter(date__month=month).filter(product__product=product).filter(product__depot=depot)
                        depot_values.append(depot_totals(entries, True))
                    months_values.append({"name":product.name, "month":month, "values":depot_values})
                    
            years.append({"year":year, "values":months_values})
            
        return years

    def get_years_revenue(self, obj):
        years = []
        for year in YEARS:
            product_values = []
            for product in Product.objects.all():
                depot_values = []    
                for depot in Depot.objects.all():
                    entries = Entry.objects.filter(date__year=year).filter(product__product=product).filter(product__depot=depot)
                    depot_values.append(depot_totals(entries))
                product_values.append({"name":product.name, "values":depot_values})
                

            years.append({"year":year, "values":product_values})
            
        return years
    
    def get_years_quantity(self, obj):
        years = []
        for year in YEARS:
            product_values = []
            for product in Product.objects.all():
                depot_values = []    
                for depot in Depot.objects.all():
                    entries = Entry.objects.filter(date__year=year).filter(product__product=product).filter(product__depot=depot)
                    depot_values.append(depot_totals(entries, True))
                product_values.append({"name":product.name, "values":depot_values})
                

            years.append({"year":year, "values":product_values})
            
        return years

    
class DepotCustomerExpandSer(ModelSerializer):
    customers_rank = SerializerMethodField()
    customers_quantity = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "customers_quantity",
            "customers_rank",
        ]

    def get_customers_rank(self, obj):
        customers = Customer.objects.all()
        
        
        years = []
        
        for year in YEARS:
            months = []
            customers_list = []
            for idx, month in enumerate(MONTHS):
                c = customer_total(year, idx)
                prods = []
                for product in Product.objects.all():
                    prod_value = []
                    for customer in customers:
                        entries = Entry.objects.filter(truck__customer=customer)
                        if entries.exists():
                            entries_sum = entries.filter(date__year=year).filter(date__month=idx+1).filter(product__product=product).aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                            
                            
                            if entries_sum["sum"] != None:
                                prod_value.append({
                                    "name":customer.name, 
                                    "location": customer.location, 
                                    "amount":entries_sum["sum"],
                                })
                    prod_value = sorted(prod_value, key=lambda d: d['amount'], reverse=True)       
                    prods.append({"name":product.name, "customers":prod_value})        

                
                months.append({"month":idx, "customers":c, "products":prods})

            for customer in customers:
                entries = Entry.objects.filter(date__year=year).filter(truck__customer=customer)
                
                previous = 0
                if entries.exists():
                    entries_sum = entries.aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                    
                    if entries_sum["sum"] != None:
                        
                        
                        customers_list.append({
                            "name":customer.name, 
                            "location": customer.location, 
                            "amount":entries_sum["sum"],
                        })
                        
            
            customers_list = sorted(customers_list, key=lambda d: d['amount'], reverse=True)
            prods = []
            for product in Product.objects.all():
                prod_value = []
                for customer in customers:
                    entries = Entry.objects.filter(truck__customer=customer)
                    if entries.exists():
                        entries_sum = entries.filter(date__year=year).filter(product__product=product).aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                        
                        
                        if entries_sum["sum"] != None:
                            prod_value.append({
                                "name":customer.name, 
                                "location": customer.location, 
                                "amount":entries_sum["sum"],
                            })
                prod_value = sorted(prod_value, key=lambda d: d['amount'], reverse=True)       
                prods.append({"name":product.name, "customers":prod_value})   
            years.append({"year":year, "customers_all":customers_list, "months":months, "products":prods})
        return years


    def get_customers_quantity(self, obj):
        customers = Customer.objects.all()
        
        
        years = []
        
        for year in YEARS:
            months = []
            customers_list = []
            for idx, month in enumerate(MONTHS):
                c = customer_total(year, idx)
                prods = []
                for product in Product.objects.all():
                    prod_value = []
                    for customer in customers:
                        entries = Entry.objects.filter(truck__customer=customer)
                        if entries.exists():
                            entries_sum = entries.filter(date__year=year).filter(date__month=idx+1).filter(product__product=product).aggregate(sum =Sum("vol_obs"))
                            
                            
                            if entries_sum["sum"] != None:
                                prod_value.append({
                                    "name":customer.name, 
                                    "location": customer.location, 
                                    "amount":entries_sum["sum"],
                                })
                    prod_value = sorted(prod_value, key=lambda d: d['amount'], reverse=True)       
                    prods.append({"name":product.name, "customers":prod_value})        

                
                months.append({"month":idx, "customers":c, "products":prods})

            for customer in customers:
                entries = Entry.objects.filter(truck__customer=customer)
                previous = 0
                if entries.exists():
                    entries_sum = entries.filter(date__year=year).aggregate(sum =Sum("vol_obs"))
                    
                    if entries_sum["sum"] != None:
                        
                        
                        customers_list.append({
                            "name":customer.name, 
                            "location": customer.location, 
                            "amount":entries_sum["sum"],
                        })
                        

            customers_list = sorted(customers_list, key=lambda d: d['amount'], reverse=True)
            prods = []
            for product in Product.objects.all():
                prod_value = []
                for customer in customers:
                    entries = Entry.objects.filter(truck__customer=customer)
                    if entries.exists():
                        entries_sum = entries.filter(date__year=year).filter(product__product=product).aggregate(sum =Sum("vol_obs"))
                        
                        
                        if entries_sum["sum"] != None:
                            prod_value.append({
                                "name":customer.name, 
                                "location": customer.location, 
                                "amount":entries_sum["sum"],
                            })
                prod_value = sorted(prod_value, key=lambda d: d['amount'], reverse=True)       
                prods.append({"name":product.name, "customers":prod_value})   
            years.append({"year":year, "customers_all":customers_list, "months":months, "products":prods})
        return years


class DepotSer(ModelSerializer):
    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
        ]

class DepotEntrySer(ModelSerializer):
    entries = SerializerMethodField()
    revenue_monthly = SerializerMethodField()
    revenue_daily = SerializerMethodField()
    quantity_monthly = SerializerMethodField()
    quantity_daily = SerializerMethodField()
    customers = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
            "revenue_monthly",
            "customers",
            "revenue_daily",
            "quantity_daily",
            "quantity_monthly",
            "entries",
            
        ]
    
    
        
    def get_customers(self, obj):
        return CustomerExpandSer(obj.customer_set.all(), many=True).data
    def get_entries(self, obj):
        return EntryCreateSer(Entry.objects.filter(product__depot=obj).order_by("-pk"), many=True).data

    def get_quantity_daily(self, obj):
        entries = Entry.objects.filter(product__depot=obj)
        return revenue_daily(entries, True)

    def get_quantity_monthly(self, obj):
        entries = Entry.objects.filter(product__depot=obj)
        return revenue(entries, True)

    def get_revenue_monthly(self, obj):
        entries = Entry.objects.filter(product__depot=obj)
        return revenue(entries)

    def get_revenue_daily(self, obj):
        entries = Entry.objects.filter(product__depot=obj)
        return revenue_daily(entries)


class DeportEntryHelper(ModelSerializer):
    entries = SerializerMethodField()
    class Meta:
        model = Depot
        fields = [
            "name",
            "entries"
        ]
    
    def get_entries(self, obj):
        return EntryCreateSer(Entry.objects.filter(product__depot=obj), many=True).data


class ProductExpandSer(ModelSerializer):
    entries = SerializerMethodField()
    entries_depot = SerializerMethodField()
    revenue_monthly = SerializerMethodField()
    revenue_daily = SerializerMethodField()
    quantity_monthly = SerializerMethodField()
    quantity_daily = SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "quantity_daily",
            "quantity_monthly",
            "revenue_daily",
            "revenue_monthly",
            "entries_depot",
            "entries",
        ]
    
    def get_quantity_daily(self, obj):
        entries = Entry.objects.filter(product__product=obj)
        return revenue_daily(entries, True)

    def get_quantity_monthly(self, obj):
        entries = Entry.objects.filter(product__product=obj)
        return revenue(entries, True)
    
    def get_revenue_daily(self, obj):
        entries = Entry.objects.filter(product__product=obj)
        return revenue_daily(entries)

    def get_revenue_monthly(self, obj):
        entries = Entry.objects.filter(product__product=obj)
        return revenue(entries)

    def get_entries_depot(self, obj):
        return DeportEntryHelper(Depot.objects.all(), many=True).data

    def get_entries(self, obj):
        return EntryCreateSer(Entry.objects.filter(product__product=obj), many=True).data

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
    depots = SerializerMethodField()
    class Meta:
        model = User
        fields = [
            "depots",
            "months",
            "revenue",
            
            
        ]
    
    def get_depots(self, obj):
        depots = Depot.objects.all()
        labels = []
        values = []
        for depot in depots:
            totals = Entry.objects.filter(truck__customer__depot=depot).filter(date__year=2022).aggregate(total=Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
            labels.append(depot.name)
            values.append(round(totals["total"],))
        return {"labels":labels, "values":values}

    def get_months(self, obj):
        products = list(set([prod.name for prod in Product.objects.all()]))
        values = []
        years = []
        available_dates = []
        for index, product in enumerate(products):
            

            totals = [v for v in Entry.objects.filter(product__product__name=product).annotate(month=ExtractMonth('date'), year=ExtractYear('date'),)
                            .order_by()
                            .values('month', 'year')
                            .annotate(total=Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                            .values('month', 'year', 'total')
            ]
            quantities = [v for v in Entry.objects.filter(product__product__name=product).annotate(month=ExtractMonth('date'), year=ExtractYear('date'),)
                            .order_by()
                            .values('month', 'year')
                            .annotate(total=Sum("vol_obs"))
                            .values('month', 'year', 'total')
            ]
            for total in totals:
                year = [idx for idx, item in enumerate(values) if item["year"] == total["year"]]
                if len(year) == 0:
                    year_ = total["year"]
                    
                    values.append({
                        "year":year_, 
                        "months":MONTHS, 
                        "products":[]
                    })
                    year = [idx for idx, item in enumerate(values) if item["year"] == total["year"]]
                    
                    for p in products:
                        values[year[0]]["products"].append({
                            "name": p,
                            "values": [0] * 12,
                            "quantities": [0] * 12,
                        })
                    values[year[0]]["products"][index]["values"][total["month"]-1] = round(total["total"] / 1000000, 2)
                else:
                    values[year[0]]["products"][index]["values"][total["month"]-1] = round(total["total"] / 1000000, 2)

            for total in quantities:
                year = [idx for idx, item in enumerate(values) if item["year"] == total["year"]]
                values[year[0]]["products"][index]["quantities"][total["month"]-1] = round(total["total"] / 1000000, 2)

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
                prods = depot.depotproduct_set.all()
                
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