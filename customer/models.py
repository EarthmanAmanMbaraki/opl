from lib2to3.pgen2 import driver
from django.db import models
from depot.models import Depot
from django.db.models.signals import post_save
from django.dispatch import receiver

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

@receiver(post_save, sender=Customer)
def create_auth_token(sender, instance=None, created=False, **kwargs):
	if created:
		Truck.objects.create(customer=instance, plate_no="default", driver="driver")