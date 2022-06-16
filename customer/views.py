from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response

# Local imports
from .models import Customer, Driver, Truck
from depot.models import Depot, DepotCustomer
from .serializers import (
    # Create serializers
    CreateCustomerSer,
    RetrieveCustomerSer,
    # Drivers serializers
    CreateDriverSer,
    # Truck Serializers
    CreateTruckSer,
    TopCustomerMonthSer,
    CustomerMonthSer,
)


# Customer Views
class CreateCustomerView(ListCreateAPIView):
    serializer_class = CreateCustomerSer
    queryset = Customer.objects.all()

    def get(self, request, *args, **kwargs):
        e = cache.get("customer", None)
        if e:
            return Response(e)
        else:
            entries = (
                Customer.objects.all().order_by("name").prefetch_related("truck_set")
            )
            serializer = RetrieveCustomerSer(entries, many=True)
            cache.set("customer", serializer.data)
            return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = CreateCustomerSer(data=request.data)

        if serializer.is_valid():
            customer = serializer.save()

            customers = (
                Customer.objects.all().order_by("name").prefetch_related("truck_set")
            )
            serializer = RetrieveCustomerSer(customers, many=True)
            cache.set("customer", serializer.data)
            return Response(serializer.data)
        else:
            print(serializer.errors)


class CreateC(ListCreateAPIView):
    serializer_class = CreateCustomerSer

    def get(self, request, *args, **kwargs):
        code = request.GET.get("code")
        name = request.GET.get("name")
        customer = Customer.objects.create(code=code, name=name)
        return Response({"status": "workd"})


class CustomerDetailView(RetrieveAPIView):
    serializer_class = CustomerMonthSer
    queryset = Customer.objects.all().prefetch_related("sale_set")

    def get(self, request, *args, **kwargs):
        e = cache.get("customer-{}".format(self.kwargs["pk"]), None)
        if e:
            return Response(e)
        else:
            customer = Customer.objects.get(pk=int(self.kwargs["pk"]))
            serializer = CustomerMonthSer(customer)
            cache.set("customer-{}".format(self.kwargs["pk"]), serializer.data)
            return Response(serializer.data)


# Driver Views
class CreateDriverView(ListCreateAPIView):
    serializer_class = CreateDriverSer
    queryset = Driver.objects.all()


# Add customer
class AddCustomer(ListCreateAPIView):
    serializer_class = CreateTruckSer

    def post(self, request, *args, **kwargs):

        customer = request.data.get("customer")
        depot = request.data.get("depot")

        if customer and depot:
            customer = Customer.objects.get(pk=int(customer))
            depot = Depot.objects.get(pk=int(depot))
            depots_customers = depot.depotcustomer_set.filter(customer=customer)
            if not depots_customers.exists():
                depot_customer = DepotCustomer.objects.create(
                    depot=depot, customer=customer
                )
            return Response({"status": "success"})
        else:
            return Response({"status": "fail"})


# Driver Views
class CreateTruckView(ListCreateAPIView):
    serializer_class = CreateTruckSer
    queryset = Truck.objects.all()

    def post(self, request, *args, **kwargs):

        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        customer = request.data.get("customer")
        plate_no = request.data.get("plate_no")

        if first_name and last_name:
            driver = Driver.objects.create(first_name=first_name, last_name=last_name)
            if customer:
                customer = Customer.objects.get(pk=int(customer))
                truck = Truck.objects.create(
                    customer=customer, driver=driver, plate_no=plate_no
                )
            else:
                customer = Customer.objects.get(name="ONE PET")
                truck = Truck.objects.create(
                    customer=customer, plate_no=plate_no, is_hired=True
                )
            customers = (
                Customer.objects.all().order_by("name").prefetch_related("sale_set")
            )
            serializer = RetrieveCustomerSer(customers, many=True)
            return Response(serializer.data)
        else:
            Response(
                {
                    "status": "failed",
                    "message": "Something went wrong check your inputs or contact admin",
                }
            )


class TopCustomerMonthView(RetrieveAPIView):
    serializer_class = TopCustomerMonthSer
    queryset = User.objects.all()

    def get_serializer_context(self):
        year = self.request.GET.get("year", None)
        month = self.request.GET.get("month", None)

        return {"year": year, "month": month}

    def get(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        e = cache.get(
            "top-customer-{}-{}".format(context["year"], context["month"]), None
        )
        if e:
            # cache.delete("top-customer")
            return Response(e)
        else:
            user = User.objects.get(pk=int(self.kwargs["pk"]))

            serializer = TopCustomerMonthSer(user, context=context)
            cache.set(
                "top-customer-{}-{}".format(context["year"], context["month"]),
                serializer.data,
            )
            return Response(serializer.data)
