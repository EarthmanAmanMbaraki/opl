import csv
import openpyxl
import xlrd
import codecs
from django.http import HttpResponse

import os
from django.conf import settings
from django.http import HttpResponse, Http404
from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser, FormParser, MultiPartParser 
from rest_framework.views import APIView
from rest_framework.status import (
	HTTP_400_BAD_REQUEST,
	HTTP_201_CREATED,
	HTTP_404_NOT_FOUND,
	)

from rest_framework.views import APIView
from rest_framework.generics import (
	# CreateAPIView,
	ListAPIView,
	# ListCreateAPIView,
	RetrieveAPIView,
	# RetrieveUpdateAPIView,
	# UpdateAPIView,
	)
from customer.models import Customer, Truck

from depot.serializers import MainBISer, ProductListSer, BISer, ProductBISer
from order.models import Entry
from customer.views import create_excel

from . models import Product, Depot


class MainAPI(RetrieveAPIView):
	serializer_class = MainBISer
	queryset = User.objects.all()
	

class ProductList(ListAPIView):
	serializer_class = ProductListSer

	def get_queryset(self):
		depot_id = self.kwargs.get("depot_id")
		products = Product.objects.filter(depot__id=int(depot_id))
		return products

class DepotBI(ListAPIView):
    serializer_class = BISer
    queryset = Depot.objects.all()

class ProductBI(ListAPIView):
	serializer_class = ProductBISer
	def get_queryset(self):
		depot_id = self.kwargs.get("depot_id")
		products = Product.objects.filter(depot__id=int(depot_id))
		return products

def check_headers(file):
	check = False
	if file.name.endswith(".csv"):
		reader = csv.reader(codecs.iterdecode(file, 'utf-8'))
		depot_title = next(reader)
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
	print(list(headers))
	print(my_headers)
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
	vol_20 = int(row[6])
	selling_price = float(row[7])
	truck = None
	customers = Customer.objects.filter(name=customer).filter(depot=depot)
	if customers.exists():
		customer_model = customers.last()
		truck = customer_model.truck_set.last()
		print(truck)
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
		print("truck fail")
		return False
	
	products = Product.objects.filter(name=product).filter(depot=depot)
	if products.exists():
		product = products.last()
	else:
		print("product fail")
		return False
	
	if save:
		entry = Entry.objects.create(
			product=product, truck=truck, date=date, 
			order_no=order_no, entry_no=entry_no, vol_obs=vol_obs, 
			vol_20=vol_20, selling_price=selling_price)
	else:
		entry = Entry(
			product=product, truck=truck, date=date, 
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
	print("worked")
	with open(f"DailyReportTemplate{depot_id}.xlsx", 'rb') as fh:
		response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
		response['Content-Disposition'] = 'inline; filename=' + "DailyReportTemplate.xlsx"
		return response
    


