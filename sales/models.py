from django.db import models
from django.core.cache import cache
from customer.models import Customer, Truck

from depot.models import Depot
from product.models import Product


class Sale(models.Model):
    # Relations
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True, blank=True)

    # Atrributes
    entry_no = models.CharField(max_length=50, null=True)
    date = models.DateField()
    is_paid = models.BooleanField(default=True)
    is_loaded = models.BooleanField(default=True)
    lpo_no = models.CharField(max_length=50, null=True)
    order_no = models.CharField(max_length=50)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    vol_obs = models.FloatField()
    vol_20 = models.FloatField(null=True, blank=True)

    def __str__(self) -> str:
        return (
            self.customer.__str__()
            + " : "
            + self.product.__str__()
            + " : "
            + self.order_no
            + " : "
            + str(self.date)
        )
