from operator import mod
from django.db import models

from depot.models import DepotProduct
from customer.models import Truck

class Entry(models.Model):
    """Entry model: Holds info about a given purchase of a product

    Fields:
        product = ForeignKey to Product model
        truck = ForeignKey to Truck model
        entry_no = str
        order_no = str
        date = date
        vol_obs = float
        vol_20 = float
        selling_price = Decimal
        is_loaded = bool

    Methods:
        1. __str__(): Display name of the model. returns (product : truck)
    """

    # Relations
    product     = models.ForeignKey(DepotProduct, on_delete=models.PROTECT, null=True, blank=True)
    truck       = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True)

    # Other fields
    entry_no        = models.CharField(max_length=50, null=True, blank=True)
    order_no        = models.CharField(max_length=50)
    date            = models.DateField()
    vol_obs         = models.FloatField()
    vol_20          = models.FloatField(blank=True, null=True)
    selling_price   = models.DecimalField(max_digits=12, decimal_places=2)

    is_loaded       = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.product.__str__() + " : " + self.truck.__str__() + " : " + str(self.date)
