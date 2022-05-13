import csv
import openpyxl
import xlrd
import codecs
from django.http import HttpResponse

from django.contrib.auth.models import User

from rest_framework.response import Response
from rest_framework.parsers import  MultiPartParser 
from rest_framework.views import APIView

from rest_framework.views import APIView
from rest_framework.generics import (
	ListAPIView,
	RetrieveAPIView,
	)
from customer.models import Customer, Truck

from depot.serializers import (
	DepotCustomerExpandSer,  
	DepotListTimeSeriesSer,
	ProductListSer, 
	DepotSer, 
	DepotMonthlySer, DepotDailySer,
	DepotMainDailySer, DepotCustomerSer, ProductDailySer, ProductMonthlySer,
	DepotCustomerExpandAllSer, DepotCustomerExpandMonthSer,
	DepotCustomer
)
from order.models import Entry
from customer.views import create_excel

from . models import DepotProduct, Product, Depot

class DepotCustomersList(ListAPIView):
	serializer_class = DepotCustomer
	queryset = Depot.objects.all()

class DepotListTimeSeriesView(RetrieveAPIView):
	serializer_class = DepotListTimeSeriesSer
	queryset = User.objects.all()
	
class DepotListView(ListAPIView):
	"""Return data for every depot, organize data by year, month and date"""
	serializer_class = DepotSer
	queryset = Depot.objects.all()

class DepotMonthlyView(ListAPIView):
	"""Return entry data for every depot, organize data by year, month and date"""
	serializer_class = DepotMonthlySer
	queryset = Depot.objects.all()

class DepotDailyView(ListAPIView):
	"""Return entry data for every depot, organize data by year, month and date"""
	serializer_class = DepotDailySer
	queryset = Depot.objects.all()

class DepotCustomerView(ListAPIView):
	"""Return entry data for every depot, organize data by year, month and date"""
	serializer_class = DepotCustomerSer
	queryset = Depot.objects.all()

class DepotMainDailyView(ListAPIView):
	"""Return entry data for every depot, organize data by year, month and date"""
	serializer_class = DepotMainDailySer
	queryset = Depot.objects.all()

class CustomerExpand(RetrieveAPIView):
	serializer_class = DepotCustomerExpandSer
	queryset = Depot.objects.all()

class CustomerExpandAll(RetrieveAPIView):
	serializer_class = DepotCustomerExpandAllSer
	queryset = Depot.objects.all()

class CustomerExpandMonth(RetrieveAPIView):
	serializer_class = DepotCustomerExpandMonthSer
	queryset = Depot.objects.all()

class ProductListView(ListAPIView):
	serializer_class = ProductListSer
	queryset = Product.objects.all()

class ProductDailyView(ListAPIView):
	serializer_class = ProductDailySer
	queryset = Product.objects.all()

class ProductMonthlyView(ListAPIView):
	serializer_class = ProductMonthlySer
	queryset = Product.objects.all()

class ProductList(ListAPIView):
	serializer_class = ProductListSer

	def get_queryset(self):
		depot_id = self.kwargs.get("depot_id")
		products = Product.objects.filter(depot__id=int(depot_id))
		return products

def check_headers(file):
	check = False
	if file.name.endswith(".csv"):
		reader = csv.reader(codecs.iterdecode(file, 'utf-8'))
		headers = next(reader)
	elif file.name.endswith(".xlsx"):
		
		wb = openpyxl.load_workbook(file)
		ws = wb.active
		reader = list(ws.iter_rows(values_only=True))
		headers = reader[1]
		reader = reader[2:]
	elif file.name.endswith(".xls"):
		workbook = xlrd.open_workbook(file_contents=file.read())
		sheet = workbook.sheet_by_index(0)
		data = [sheet.row_values(rowx) for rowx in range(sheet.nrows)]
		headers = data[1]
		reader = data[2:]

	my_headers = ["DATE", "PRODUCT", "CUSTOMER", "ORDER NO", "ENTRY NO", "VOL OBS", "VOL 20", "SELLING PRICE"]
	if list(headers) == my_headers:
		check = True

	return check, reader

def upload(row, depot, save):
	date = row[0]
	product = row[1]
	customer = row[2]
	order_no = row[3]
	entry_no = row[4]
	vol_obs = int(row[5])
	vol_20 = int(row[6]) if row[6] != None else row[6]
	selling_price = float(row[7])
	truck = None
	customers = Customer.objects.filter(name=customer).filter(depot=depot)
	if customers.exists():
		customer_model = customers.last()
		truck = customer_model.truck_set.last()
		if not truck:
			truck = Truck.objects.create(customer=customer_model, plate_no="default", driver="default")
		# if trucks.exists():
		# 	truck = trucks.last()
		# else:
		# 	if save:
		# 		truck = Truck.objects.create(customer=customer_model, plate_no=truck_no, driver=customer)
		# 	else:
		# 		truck = Truck(customer=customer_model, plate_no=truck_no, driver=customer)
		
	if truck == None:
		return False
	
	depot_product = DepotProduct.objects.filter(product__name=product).get(depot=depot)

	
	if save:
		entry = Entry.objects.create(
			product=depot_product, truck=truck, date=date, 
			order_no=order_no, entry_no=entry_no, vol_obs=vol_obs, 
			vol_20=vol_20, selling_price=selling_price)
	else:
		entry = Entry(
			product=depot_product, truck=truck, date=date, 
			order_no=order_no, entry_no=entry_no, vol_obs=vol_obs, 
			vol_20=vol_20, selling_price=selling_price)
	return True

class UploadExcel(APIView):
	parser_classes = (MultiPartParser, )
	def post(self, request, *args, **kwargs):
		file = request.FILES['file']
		check, reader = check_headers(file)
		depot = Depot.objects.filter(pk=int(self.kwargs.get("depot_id")))
		if not depot.exists():
			return Response({"status":"fail", "message": "An error occured contact admin."})
		elif check:
			depot = depot.last()
			for row in reader:
				succesful = upload(row, depot, save=False)
				if succesful == False:
					return Response({"status":"fail", "message": "Error in the data. Please check or contact admin."})
				succesful = upload(row, depot, save=True)
				
			return Response({"status":"success", "message": "Uploaded successful"})
		else:
			
			return Response({"status":"fail", "message": "Make sure the file used is correct."})
				
def download(request, depot_id):
	create_excel(Depot.objects.get(pk=int(depot_id)))
	with open(f"DailyReportTemplate{depot_id}.xlsx", 'rb') as fh:
		response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
		response['Content-Disposition'] = 'inline; filename=' + "DailyReportTemplate.xlsx"
		return response
    


