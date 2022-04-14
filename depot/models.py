from django.db import models
from django.contrib.auth.models import User # User setting.AUTH_USER_MODEL when need to integrate with other apps

class Depot(models.Model):
    """Depot model: this will hold the information about a depot.
    Fields:
        name 
        country (optional)
        county (optional)
        area (optional) 

    Methods:
        1. __str__() => display name of the model. returns (depot name)
    """
    name    = models.CharField(max_length=150, unique=True)
    country = models.CharField(max_length=50, null=True)
    county  = models.CharField(max_length=50, null=True)
    area    = models.CharField(max_length=50, null=True)

    def __str__(self) -> str:
        return self.name

class DepotManager(models.Model):
    """Deport manager model: this is a helper model which links the user and the depot.
    One user can be a manager in several depots and one depot can have more than one manager.
    
    Fields:
        user = ForeignKey to User model
        depot = ForeignKey to Depot model
    methods:
        1. __str__() => Display name of the model. returns (depot : user)
    """

    user    = models.ForeignKey(User, on_delete=models.PROTECT)
    depot   = models.ForeignKey(Depot, on_delete=models.PROTECT)

    def __str__(self) -> str:
        return self.depot.__str__() + " : " + self.user.__str__()

class Product(models.Model):
    """Product model: This model holds the information of a product this was inspired by the fact
    that one depot handles more than one product

    Fields:
        depot = ForeignKey to Depot model
        name = str

    Methods:
        1. __str__(): Display name of the model. returns (product name : depot)
    """

    depot   = models.ForeignKey(Depot, on_delete=models.PROTECT)
    name    = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name + " : " + self.depot.__str__()

