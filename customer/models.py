from django.db import models
from depot.models import Depot

class Customer(models.Model):
    """Customer Model: This will hold information about a customer.
    You can add more field or divide the table when need arises

    Fields:
        name = str

    Methods:
        1. __str__(): Display name of the model. returns (customer name)
    """
    depot       = models.ForeignKey(Depot, on_delete=models.PROTECT)
    name        = models.CharField(max_length=100)
    location    = models.CharField(max_length=100, null=True)

    def __str__(self) -> str:
        return self.name
class Truck(models.Model):
    """Truck model: hold information about a customer truck

    Fields:
        customer = ForeignKey to Customer
        plate_no = str (optional)
        driver_name = str (Information about a driver may be removed to another table if more info is needed)

    Methods:
        1. __str__(): Display name of the model. returns (driver name : customer name)
    """

    # Relations
    customer    = models.ForeignKey(Customer, on_delete=models.CASCADE)

    # Other fields
    plate_no    = models.CharField(max_length=20, null=True)
    driver      = models.CharField(max_length=150)

    def __str__(self) -> str:
        return self.driver + " : " + self.customer.__str__()