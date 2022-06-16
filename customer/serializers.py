from django.contrib.auth.models import User
from django.db.models import F, FloatField, Sum, Count
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
)
from .models import Customer, Driver, Truck
from sales.models import Sale

# Customer Serializers
class CreateCustomerSer(ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "code",
            "name",
        ]


class RetrieveCustomerSer(ModelSerializer):
    """Handle retrieve and update requests

    Used in:
        RetrieveSaleSer -> sales.serializers
    """

    trucks = SerializerMethodField()

    class Meta:
        model = Customer
        fields = ["id", "code", "name", "trucks"]

    def get_trucks(self, obj):
        return RetrieveTruckSer(obj.truck_set, many=True).data


# Drivers Serializers
class CreateDriverSer(ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "first_name",
            "last_name",
        ]


class RetrieveDriverSer(ModelSerializer):
    """Handle retrieve of driver

    Used:
        RetrieveTruckSer -> customer.serializers
    """

    class Meta:
        model = Driver
        fields = [
            "id",
            "first_name",
            "last_name",
        ]


# Truck Serializers
class CreateTruckSer(ModelSerializer):
    class Meta:
        model = Truck
        fields = [
            "driver",
            "plate_no",
            "is_hired",
        ]


class RetrieveTruckSer(ModelSerializer):
    """Handle retrieve and update requests

    Used in:
        RetrieveSaleSer -> sales.serializers
    """

    driver = SerializerMethodField()

    class Meta:
        model = Truck
        fields = [
            "id",
            "driver",
            "plate_no",
            "is_hired",
        ]

    def get_driver(self, obj):
        return RetrieveDriverSer(obj.driver).data


class TopCustomerMonthSer(ModelSerializer):
    revenue = SerializerMethodField()
    quantity = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "revenue",
            "quantity",
        ]

    def calc(self, quantity, year, month):
        sales = Sale.objects.filter(date__year=year).select_related()
        if quantity:
            if month != "False":
                totals = (
                    sales.values("customer__name", "date__month")
                    .annotate(sum=Sum("vol_obs"))
                    .values("customer__name", "date__month", "sum")
                )
            else:
                print("in else")
                totals = (
                    sales.values("customer__name")
                    .annotate(sum=Sum("vol_obs"))
                    .values("customer__name", "sum")
                )

        else:
            if month != "False":
                totals = (
                    sales.values("customer__name", "date__month")
                    .annotate(
                        sum=Sum(
                            F("selling_price") * F("vol_obs"), output_field=FloatField()
                        )
                    )
                    .values("customer__name", "date__month", "sum")
                )
            else:
                totals = (
                    sales.values("customer__name")
                    .annotate(
                        sum=Sum(
                            F("selling_price") * F("vol_obs"), output_field=FloatField()
                        )
                    )
                    .values("customer__name", "sum")
                )

        totals = totals.order_by("-sum")
        if month != "False":
            months = []
            for month in range(1, 13):
                customer_month = totals.filter(date__month=month)
                months.append({"month": month, "customers": customer_month})
            return months
        return totals

    def get_revenue(self, obj):
        year = self.context["year"]
        month = self.context["month"]
        return self.calc(False, year, month)

    def get_quantity(self, obj):
        year = self.context["year"]
        month = self.context["month"]
        return self.calc(True, year, month)


class CustomerMonthSer(ModelSerializer):
    revenue = SerializerMethodField()
    quantity = SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "revenue",
            "quantity",
        ]

    def calc(self, obj, quantity=False):
        years = [year[0] for year in set(obj.sale_set.values_list("date__year"))]
        y = []
        for year in years:
            sales = obj.sale_set.filter(date__year=year)
            if quantity:

                totals = (
                    sales.values("date__month")
                    .annotate(sum=Sum("vol_obs"), count=Count("id"))
                    .values("date__month", "sum", "count")
                )
            else:
                totals = (
                    sales.values("date__month")
                    .annotate(
                        sum=Sum(
                            F("selling_price") * F("vol_obs"), output_field=FloatField()
                        ),
                        count=Count("id"),
                    )
                    .values("date__month", "sum", "count")
                )
            totals = totals.order_by("-sum")
            months = []

            months.append({"month": totals})
            y.append({"year": year, "months": totals})
        return y

    def get_revenue(self, obj):
        return self.calc(obj)

    def get_quantity(self, obj):
        return self.calc(obj, True)
