import csv
from django.shortcuts import render
from rest_framework.response import Response

from rest_framework.generics import (
	ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
	)
from . models import Entry
from customer.models import Truck
from depot.models import Product

from order.serializer import (
    EntryCreateSer, EntryListSer,
)

def excel_upload(request):
    with open('ago.csv', 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)
        print(headers)
        for row in reader:
            date = row[0]
            order_no = row[1]
            truck_no = row[2]
            entry_no = row[3]
            selling_price = float(row[4])
            vol_obs = int(row[5])
            vol_20 = int(row[6])

            truck = Truck.objects.filter(plate_no=truck_no)[0]

            product = Product.objects.filter(name="AGO").first()

            entry = Entry.objects.create(date=date, product=product, truck=truck, order_no=order_no, entry_no=entry_no, selling_price=selling_price, vol_obs=vol_obs, vol_20=vol_20)

    with open('pms.csv', 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)
        print(headers)
        for row in reader:
            date = row[0]
            order_no = row[1]
            truck_no = row[2]
            entry_no = row[3]
            selling_price = float(row[4])
            vol_obs = int(row[5])
            vol_20 = int(row[6])

            truck = Truck.objects.filter(plate_no=truck_no)[0]

            product = Product.objects.filter(name="PMS").first()

            entry = Entry.objects.create(date=date, product=product, truck=truck, order_no=order_no, entry_no=entry_no, selling_price=selling_price, vol_obs=vol_obs, vol_20=vol_20)

    return render(request, "./upload.html")

class CreateEntry(ListCreateAPIView):
    serializer_class = EntryCreateSer
    queryset = Entry.objects.all()

    def get(self, request, *args, **kwargs):
        entries = Entry.objects.all().order_by("-date")
        print(len(entries))
        serializer = EntryListSer(entries, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = EntryCreateSer(data=request.data)

        if serializer.is_valid():
            entry = serializer.save()
            serializer = EntryCreateSer(entry)
            return Response(serializer.data)
        else:
            print(serializer.errors)

class UpdateEntry(RetrieveUpdateDestroyAPIView):
    serializer_class = EntryCreateSer
    queryset = Entry.objects.all()

