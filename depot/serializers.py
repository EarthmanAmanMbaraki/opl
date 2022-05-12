from calendar import month
from dataclasses import field
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
from customer.serializers import CustomerExpandSer, CustomerMinExpandSer
from order.models import Entry
from order.serializer import EntryCreateSer


from . models import DepotProduct, Product, Depot

class DepotCustomer(ModelSerializer):
    customers = SerializerMethodField()
    products = SerializerMethodField()
    class Meta:
        model = Depot
        fields =[
            "id",
            "name",
            "customers",
            "products",
        ]

    def get_products(self, obj):
        products = []
        for product in obj.depotproduct_set.all():
            products.append({"name": product.product.name, "id":product.id})
        return products
        
    def get_customers(self, obj):
        customers = []
        for customer in obj.customer_set.all():
            customers.append({"name": customer.name, "id":customer.truck_set.last().id})
        return customers

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
YEARS = [2022, 2021]

def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without truncateing'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))
    
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
        all_total = 0
        filtered_totals = [total for total in totals if total['year'] == year]
        for month in filtered_totals:
            total = month["total"] if quantity else truncate(month['total']/1000000, 2)
            months.append({"month":month["month"], "total":total})
            all_total += total
        
        years.append({"year":year, "months":MONTHS, "data":months, "total":truncate(all_total, 2)})

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
            "sum":  total["sum"] if quantity == True else truncate(total["sum"]/1000000, 2)
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


class DepotCustomerExpandMonthSer(ModelSerializer):
    customers_rank = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "customers_rank",
        ]

    def get_customers_rank(self, obj):
        customers = Customer.objects.all()
        years = []
        for year in YEARS:
            months = []
            
            for index, month in enumerate(MONTHS):
                
                prods = []
                c = []
                c_quantity = []
                for prod_index, product in enumerate(Product.objects.all()):
                    prod_value = []
                    prod_value_quantity = []
                    for idx, customer in enumerate(customers):
                        entries = Entry.objects.filter(truck__customer=customer).filter(date__year=year).filter(date__month=index+1).filter(product__product=product)
                        if entries.exists():
                            entries_sum = entries.aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                            entries_sum_quantity = entries.aggregate(sum =Sum("vol_obs"))
                            if entries_sum["sum"] != None:
                                prod_value.append({
                                    "name":customer.name, 
                                    "location": customer.location, 
                                    "amount":entries_sum["sum"],
                                })
                            
                            if entries_sum_quantity["sum"] != None:
                                prod_value_quantity.append({
                                    "name":customer.name, 
                                    "location": customer.location, 
                                    "amount":entries_sum_quantity["sum"],
                                })
                       
                        if prod_index == 0:
                            entries = Entry.objects.filter(truck__customer=customer)
                            if entries.exists():
                                entries_sum = entries.filter(date__year=year).filter(date__month=index+1).aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                                entries_sum_quantity = entries.filter(date__year=year).filter(date__month=index+1).aggregate(sum =Sum('vol_obs'))
                                if entries_sum["sum"] != None:
                                    c.append({
                                        "name":customer.name, 
                                        "location": customer.location, 
                                        "amount":entries_sum["sum"],
                                    })
                                if entries_sum_quantity["sum"] != None:
                                    c_quantity.append({
                                        "name":customer.name, 
                                        "location": customer.location, 
                                        "amount":entries_sum_quantity["sum"],
                                    })
                            c = sorted(c, key=lambda d: d['amount'], reverse=True)
                            c_quantity = sorted(c_quantity, key=lambda d: d['amount'], reverse=True)
                    
                    prod_value = sorted(prod_value, key=lambda d: d['amount'], reverse=True) 
                    prod_value_quantity = sorted(prod_value_quantity, key=lambda d: d['amount'], reverse=True)       
                    prods.append({
                        "name":product.name, 
                        "customers_revenue":prod_value, 
                        "customers_quantity":prod_value_quantity,
                        })
               
                months.append({"month":index, "customers_revenue":c, "customers_quantity":c_quantity, "products":prods})

            years.append({"year":year, "months":months})
        return years

def depot_totals(entries, quantity=False):
    if quantity:
        total = sum([entry.vol_obs for entry in entries])
    else:
        total = sum([(entry.vol_obs * float(entry.selling_price)) for entry in entries])
        total = truncate(total/1000000, 2)
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


class DepotCustomerExpandAllSer(ModelSerializer):
    customers_rank = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "customers_rank",
        ]

    def get_customers_rank(self, obj):
        customers = Customer.objects.all()
        years = []
        for year in YEARS:
            customers_list = []
            customers_quantity_list = []
            for customer in customers:
                entries = Entry.objects.filter(date__year=year).filter(truck__customer=customer)
                if entries.exists():
                    entries_sum = entries.aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
                    entries_sum_quantity = entries.filter(date__year=year).aggregate(sum =Sum("vol_obs"))
                    if entries_sum["sum"] != None:
                        customers_list.append({
                            "name":customer.name, 
                            "location": customer.location, 
                            "amount":entries_sum["sum"],
                        })

                    if entries_sum_quantity["sum"] != None:
                        customers_quantity_list.append({
                            "name":customer.name, 
                            "location": customer.location, 
                            "amount":entries_sum_quantity["sum"],
                        })
            customers_list = sorted(customers_list, key=lambda d: d['amount'], reverse=True)  
            customers_quantity_list = sorted(customers_quantity_list, key=lambda d: d['amount'], reverse=True)  
            years.append({"year":year, "customers_revenue":customers_list, "customers_quantity":customers_quantity_list})
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


class DepotMonthlySer(ModelSerializer):
    revenue_monthly = SerializerMethodField()
    quantity_monthly = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
            "revenue_monthly",
            "quantity_monthly",
            
        ]
    
    def get_quantity_monthly(self, obj):
        entries = Entry.objects.filter(product__depot=obj)
        return revenue(entries, True)

    def get_revenue_monthly(self, obj):
        entries = Entry.objects.filter(product__depot=obj)
        return revenue(entries)


class DepotDailySer(ModelSerializer):
    revenue_daily = SerializerMethodField()
    quantity_daily = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
            "revenue_daily",
            "quantity_daily",
            
        ]

    def get_quantity_daily(self, obj):
        entries = Entry.objects.filter(product__depot=obj)
        return revenue_daily(entries, True)

    def get_revenue_daily(self, obj):
        entries = Entry.objects.filter(product__depot=obj)
        return revenue_daily(entries)


class DepotMainDailySer(ModelSerializer):
    depot_revenue_daily = SerializerMethodField()
    depot_quantity_daily = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
            "depot_revenue_daily",
            "depot_quantity_daily",     
        ]
    
    def get_depot_revenue_daily(self, obj):
        products = []
        for product in obj.depotproduct_set.all():
            entries = Entry.objects.filter(product__depot=obj).filter(product=product)
            products.append({"name":product.product.name, "values":revenue_daily(entries)})
        return products

    def get_depot_quantity_daily(self, obj):
        products = []
        for product in obj.depotproduct_set.all():
            entries = Entry.objects.filter(product__depot=obj).filter(product=product)
            products.append({"name":product.product.name, "values":revenue_daily(entries, True)})
        return products

class DepotCustomerSer(ModelSerializer):
   
    customers = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
            "customers",  
        ]
    
    
        
    def get_customers(self, obj):
        return CustomerMinExpandSer(obj.customer_set.all(), many=True).data


class DepotEntrySer(ModelSerializer):
    entries = SerializerMethodField()
    revenue_monthly = SerializerMethodField()
    revenue_daily = SerializerMethodField()
    quantity_monthly = SerializerMethodField()
    quantity_daily = SerializerMethodField()
    customers = SerializerMethodField()
    depot_revenue_daily = SerializerMethodField()
    depot_quantity_daily = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
            "revenue_monthly",
            "depot_revenue_daily",
            "depot_quantity_daily",
            "revenue_daily",
            "customers",
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
    
    def get_depot_revenue_daily(self, obj):
        products = []
        for product in obj.depotproduct_set.all():
            entries = Entry.objects.filter(product__depot=obj).filter(product=product)
            products.append({"name":product.product.name, "values":revenue_daily(entries)})
        return products

    def get_depot_quantity_daily(self, obj):
        products = []
        for product in obj.depotproduct_set.all():
            entries = Entry.objects.filter(product__depot=obj).filter(product=product)
            products.append({"name":product.product.name, "values":revenue_daily(entries, True)})
        return products

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

class ProductDailySer(ModelSerializer):
    revenue_daily = SerializerMethodField()
    quantity_daily = SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "quantity_daily",
            "revenue_daily",
        ]
    
    def get_quantity_daily(self, obj):
        entries = Entry.objects.filter(product__product=obj)
        return revenue_daily(entries, True)

    def get_revenue_daily(self, obj):
        entries = Entry.objects.filter(product__product=obj)
        return revenue_daily(entries)

class ProductMonthlySer(ModelSerializer):
    revenue_monthly = SerializerMethodField()
    quantity_monthly = SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "quantity_monthly",
            "revenue_monthly",
        ]

    def get_quantity_monthly(self, obj):
        entries = Entry.objects.filter(product__product=obj)
        return revenue(entries, True)
    
    def get_revenue_monthly(self, obj):
        entries = Entry.objects.filter(product__product=obj)
        return revenue(entries)


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
            values.append(truncate(totals["total"],2))
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
                    values[year[0]]["products"][index]["values"][total["month"]-1] = truncate(total["total"] / 1000000, 2)
                else:
                    values[year[0]]["products"][index]["values"][total["month"]-1] = truncate(total["total"] / 1000000, 2)

            for total in quantities:
                year = [idx for idx, item in enumerate(values) if item["year"] == total["year"]]
                values[year[0]]["products"][index]["quantities"][total["month"]-1] = truncate(total["total"] / 1000000, 2)

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
                                    values[idx][1] += truncate(totals[index]["sum"] / 1000000, 2)
                                    quantity_value[idx][1] += quantity_totals[index]["sum"]
                        else:
                            available_dates.append(date)
                            values.append([timestamp, truncate(totals[index]["sum"] / 1000000, 2)])
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
                    
                    values.append(truncate(totals[index]["sum"] / 1000000, 2))
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
                months_values.append(truncate(totals["sum"]/1000000, 2) if totals["sum"] != None else 0)
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
            
            "main",
            "months",
        ]
    def get_months(self, obj):
        months_values = []
        orders = []
        for month in range(1, 13):
            
            totals = obj.entry_set.filter(date__month=month).order_by('date').aggregate(sum =Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
            orders_totals = obj.entry_set.filter(date__month=month).order_by('date').aggregate(count =Count("id"))
            months_values.append(truncate(totals["sum"]/1000000, 2) if totals["sum"] != None else 0)
            orders.append(orders_totals["count"])
        data = {"name":obj.product.name, "values": months_values, "orders":orders}

        
        return {"months":MONTHS, "data": data}
    

    def get_main(self, obj):
        totals = obj.entry_set.filter().values('date').order_by('-date').annotate(sum=Sum(F("selling_price") * F('vol_obs'), output_field=FloatField()))
        dates = []
        values = []
        for total in totals:
            date = int(datetime.datetime.combine(total["date"], datetime.datetime.min.time()).timestamp())
            value = truncate(total["sum"]/1000000, 2)
            dates.append(date*1000)
            values.append([date*1000, value])

        return {"dates": dates, "values":values, "total": totals}