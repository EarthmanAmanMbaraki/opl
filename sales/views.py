import datetime
import csv
import openpyxl
import xlrd
import codecs
import threading
from django.shortcuts import render
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from customer.models import Customer, Truck
from depot.models import Depot
from product.models import Product

from sales.resources import SaleResource

# Local imports
from .models import Sale
from .serializers import CreateSaleSer, RetrieveSaleSer

from tablib import Dataset


def simple_upload(request):
    if request.method == "POST":
        person_resource = SaleResource()
        dataset = Dataset()
        new_persons = request.FILES["myfile"]

        imported_data = dataset.load(new_persons.read())
        result = person_resource.import_data(
            dataset, dry_run=True
        )  # Test the data import
        print(result.has_errors())
        if not result.has_errors():
            person_resource.import_data(dataset, dry_run=False)  # Actually import now

    return render(request, "simple_upload.html")


class CreateSaleView(ListCreateAPIView):
    serializer_class = CreateSaleSer
    queryset = Sale.objects.all().select_related()

    def get(self, request, *args, **kwargs):
        start_date = request.GET.get("start_date", None)
        end_date = request.GET.get("end_date", None)
        if start_date != None and end_date != None:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            entries = (
                Sale.objects.filter(date__gte=start_date)
                .filter(date__lte=end_date)
                .order_by("-date")
                .select_related()
            )
        else:
            entries = Sale.objects.all().select_related()

        serializer = RetrieveSaleSer(entries, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = CreateSaleSer(data=request.data)

        if serializer.is_valid():
            sale = serializer.save()
            start_date = request.GET.get("start_date", None)
            end_date = request.GET.get("end_date", None)
            if start_date != None and end_date != None:
                start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                entries = (
                    Sale.objects.filter(date__gte=start_date)
                    .filter(date__lte=end_date)
                    .order_by("-date")
                    .select_related()
                )
            else:
                entries = Sale.objects.all().select_related()

            serializer = RetrieveSaleSer(entries, many=True)
            return Response(serializer.data)
        else:
            print(serializer.errors)


class RetrieveSaleView(RetrieveUpdateAPIView):
    serializer_class = RetrieveSaleSer
    queryset = Sale.objects.all()


# class UploadExcel(APIView):
#     parser_classes = (MultiPartParser,)

#     def post(self, request, *args, **kwargs):
#         sale_resource = SaleResource()
#         dataset = Dataset()
#         file = request.FILES["file"]
#         r = file.read()
#         imported_data = dataset.load(r)
#         result = sale_resource.import_data(
#             dataset, dry_run=True
#         )  # Test the data import
#         if not result.has_errors():
#             # sale_resource.import_data(dataset, dry_run=False)  # Actually import now
#             return Response(
#                 {"status": status.HTTP_201_CREATED, "message": "Upload successful"}
#             )
#         return Response(
#             {
#                 "status": status.HTTP_403_FORBIDDEN,
#                 "message": "Check your file format. If error persist contact admin",
#             }
#         )


def check_headers(file):
    check = False
    if file.name.endswith(".csv"):
        reader = csv.reader(codecs.iterdecode(file, "utf-8"))
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

    my_headers = [
        "DATE",
        "PRODUCT",
        "CUSTOMER",
        "TRUCK",
        "ORDER NO",
        "LPO_NO",
        "ENTRY NO",
        "VOL OBS",
        "VOL 20",
        "SELLING PRICE",
        "PAYMENT",
    ]
    if list(headers) == my_headers:
        check = True

    return check, reader


def upload(row, depot, save):
    date = row[0]
    product = row[1]
    customer = row[2]
    truck = row[3]
    order_no = row[4]
    lpo_no = row[5]
    entry_no = row[6]
    vol_obs = int(row[7])
    vol_20 = int(row[8]) if row[8] != None else row[8]
    selling_price = float(row[9])
    is_paid = True if row[10] == "Yes" else False

    customer = Customer.objects.get(name=customer)
    truck = Truck.objects.get(plate_no=truck)
    product = Product.objects.get(name=product)

    if save:
        print(truck)
        sale = Sale.objects.create(
            product=product,
            depot=depot,
            truck=truck,
            customer=customer,
            date=date,
            order_no=order_no,
            lpo_no=lpo_no,
            entry_no=entry_no,
            vol_obs=vol_obs,
            vol_20=vol_20,
            selling_price=selling_price,
            is_paid=is_paid,
        )
    else:
        sale = Sale(
            product=product,
            depot=depot,
            truck=truck,
            date=date,
            order_no=order_no,
            lpo_no=lpo_no,
            entry_no=entry_no,
            vol_obs=vol_obs,
            vol_20=vol_20,
            selling_price=selling_price,
            is_paid=is_paid,
        )
    return True


def up(reader, depot, save):
    for row in reader:
        succesful = upload(row, depot, save=save)
        if not succesful:
            return False
    return True


class HandleExcelUpload(threading.Thread):
    def __init__(self, reader, depot):
        self.reader = reader
        self.depot = depot

        threading.Thread.__init__(self)

    def run(self):
        up(self.reader, self.depot, True)


class UploadExcel(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, *args, **kwargs):
        file = request.FILES["file"]
        check, reader = check_headers(file)
        depot = Depot.objects.filter(pk=int(self.kwargs.get("depot_id")))
        if not depot.exists():
            return Response(
                {"status": "fail", "message": "An error occured contact admin."}
            )
        elif check:
            depot = depot.last()

            succesful = up(reader, depot, save=False)
            if succesful == False:
                return Response(
                    {
                        "status": "fail",
                        "message": "Error in the data. Please check or contact admin.",
                    }
                )
            HandleExcelUpload(reader, depot).start()

            return Response({"status": "success", "message": "Uploaded successful"})
        else:

            return Response(
                {"status": "fail", "message": "Make sure the file used is correct."}
            )
