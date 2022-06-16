import datetime
from django.db.models import F, FloatField, Sum, Count
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
)

# Local imports
from product.models import Product
from .models import Depot


class RetrieveDepotSer(ModelSerializer):
    """Handle retrieve of depot

    Used:
        RetrieveSaleSer -> sale/serializers
    """

    class Meta:
        model = Depot
        fields = ["id", "name"]


class DepotMonthSer(ModelSerializer):
    revenue = SerializerMethodField()
    quantity = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
            "revenue",
            "quantity",
        ]

    def calc(self, obj, quantity, year):

        if quantity:
            totals = (
                obj.sale_set.filter(date__year=year)
                .values("date__month")
                .annotate(sum=Sum("vol_obs"))
                .values("date__month", "sum")
            )
        else:
            totals = (
                obj.sale_set.filter(date__year=year)
                .values("date__year", "date__month")
                .annotate(
                    sum=Sum(
                        F("selling_price") * F("vol_obs"), output_field=FloatField()
                    )
                )
                .values("date__month", "sum")
            )
        # total = totals.aggregate(total=Sum("sum"))

        return totals

    def get_revenue(self, obj):
        year = self.context.get("year", None)
        return self.calc(obj, False, year)

    def get_quantity(self, obj):
        year = self.context.get("year", None)
        return self.calc(obj, True, year)


class DepotProductMonthSer(ModelSerializer):
    revenue = SerializerMethodField()
    quantity = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
            "revenue",
            "quantity",
        ]

    def calc(self, obj, quantity, year):
        products = Product.objects.all()
        sales = obj.sale_set.filter(date__year=year)
        prods = []
        for product in products:
            if quantity:
                totals = (
                    sales.filter(product=product)
                    .values("date__year", "date__month")
                    .annotate(sum=Sum("vol_obs"))
                    .values("date__month", "sum")
                )
            else:
                totals = (
                    sales.filter(product=product)
                    .values("date__year", "date__month")
                    .annotate(
                        sum=Sum(
                            F("selling_price") * F("vol_obs"),
                            output_field=FloatField(),
                        )
                    )
                    .values("date__month", "sum")
                )
            prods.append({"name": product.name, "months": totals})

        return prods

    def get_revenue(self, obj):
        year = self.context["year"]
        return self.calc(obj, False, year)

    def get_quantity(self, obj):
        year = self.context["year"]
        return self.calc(obj, True, year)


class DepotSeriesSer(ModelSerializer):
    revenue = SerializerMethodField()
    quantity = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
            "revenue",
            "quantity",
        ]

    def calc(self, obj, quantity, start_date=None, end_date=None):

        if start_date and end_date:
            sales = obj.sale_set.filter(date__gte=start_date).filter(date__lte=end_date)
        else:
            sales = obj.sale_set.all()

        if quantity:
            totals = sales.values("date").annotate(sum=Sum("vol_obs"))
        else:
            totals = sales.values("date").annotate(
                sum=Sum(F("selling_price") * F("vol_obs"), output_field=FloatField())
            )
        t = []
        for total in totals.order_by("-date"):
            timestamp = (
                int(
                    datetime.datetime.combine(
                        total["date"], datetime.datetime.min.time()
                    ).timestamp()
                )
                * 1000
            )
            t.append(
                {"date": total["date"], "timestamp": timestamp, "sum": total["sum"]}
            )
        return t

    def get_revenue(self, obj):
        start_date = self.context["start_date"]
        end_date = self.context["end_date"]
        if start_date and end_date:
            return self.calc(obj, False, start_date, end_date)
        return self.calc(obj, False)

    def get_quantity(self, obj):
        start_date = self.context["start_date"]
        end_date = self.context["end_date"]
        if start_date and end_date:
            return self.calc(obj, True, start_date, end_date)
        return self.calc(obj, True)


class DepotProductSeriesSer(ModelSerializer):
    revenue = SerializerMethodField()
    quantity = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
            "revenue",
            "quantity",
        ]

    def calc(self, obj, quantity, start_date, end_date):
        products = [
            product[0] for product in set(obj.sale_set.values_list("product__name"))
        ]
        prods = []
        for product in products:
            if start_date and end_date:
                sales = (
                    obj.sale_set.filter(product__name=product)
                    .filter(date__gte=start_date)
                    .filter(date__lte=end_date)
                )
            else:
                sales = obj.sale_set.filter(product__name=product)
            if quantity:
                totals = sales.values("date").annotate(sum=Sum("vol_obs"))
            else:
                totals = sales.values("date").annotate(
                    sum=Sum(
                        F("selling_price") * F("vol_obs"), output_field=FloatField()
                    )
                )
            t = []
            for total in totals:
                timestamp = (
                    int(
                        datetime.datetime.combine(
                            total["date"], datetime.datetime.min.time()
                        ).timestamp()
                    )
                    * 1000
                )
                t.append(
                    {"date": total["date"], "timestamp": timestamp, "sum": total["sum"]}
                )
            prods.append({"name": product, "data": t})
        return prods

    def get_revenue(self, obj):
        start_date = self.context["start_date"]
        end_date = self.context["end_date"]
        if start_date and end_date:
            return self.calc(obj, False, start_date, end_date)
        return self.calc(obj, False)

    def get_quantity(self, obj):
        start_date = self.context["start_date"]
        end_date = self.context["end_date"]
        if start_date and end_date:
            return self.calc(obj, True, start_date, end_date)
        return self.calc(obj, True)


class DepotCustomerMonthSer(ModelSerializer):
    revenue = SerializerMethodField()
    quantity = SerializerMethodField()

    class Meta:
        model = Depot
        fields = [
            "id",
            "name",
            "revenue",
            "quantity",
        ]

    def calc(self, obj, quantity, year, month):

        sales = obj.sale_set.filter(date__year=year)
        if quantity:
            if month != 13:
                totals = (
                    sales.filter(date__month=month)
                    .values("customer__name", "date__month")
                    .annotate(sum=Sum("vol_obs"), count=Count("id"))
                    .values("customer__name", "date__month", "sum", "count")
                )
            else:
                totals = (
                    sales.values("customer__name")
                    .annotate(sum=Sum("vol_obs"), count=Count("id"))
                    .values("customer__name", "sum", "count")
                )

        else:
            if month != 13:
                totals = (
                    sales.filter(date__month=month)
                    .values("customer__name", "date__month")
                    .annotate(
                        sum=Sum(
                            F("selling_price") * F("vol_obs"), output_field=FloatField()
                        ),
                        count=Count("id"),
                    )
                    .values("customer__name", "date__month", "sum", "count")
                )
            else:
                totals = (
                    sales.values("customer__name")
                    .annotate(
                        sum=Sum(
                            F("selling_price") * F("vol_obs"), output_field=FloatField()
                        ),
                        count=Count("id"),
                    )
                    .values("customer__name", "sum", "count")
                )

        totals = totals.order_by("-sum")

        return totals

    def get_revenue(self, obj):
        year = self.context["year"]
        month = self.context["month"]
        return self.calc(obj, False, year, month)

    def get_quantity(self, obj):
        year = self.context["year"]
        month = self.context["month"]
        return self.calc(obj, True, year, month)
