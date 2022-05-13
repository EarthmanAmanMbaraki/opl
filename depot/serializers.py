import datetime
from django.contrib.auth.models import User
from django.db.models import Sum, F, FloatField, Count
from django.db.models.functions import ExtractMonth, ExtractYear
from rest_framework.serializers import (
	ModelSerializer,
    Serializer, 
	SerializerMethodField,	
	)

from customer.models import Customer
from customer.serializers import CustomerExpandSer, CustomerMinExpandSer
from order.models import Entry
from order.serializer import EntryCreateSer
from . models import Product, Depot

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
        total = truncate(total/1000000, 2)
    return total

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

class ProductListSer(ModelSerializer):

    class Meta:
        model = Product
        fields = [
            "id",
            "name",

        ]

