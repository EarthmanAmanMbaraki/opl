from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache

from customer.models import Customer


class Depot(models.Model):

    # Attributes
    name = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        super(Customer, self).save(*args, **kwargs)
        cache.delete("depot")
        # cache.delete("customer-{}".format(self.pk))

    def __str__(self) -> str:
        return self.name


class DepotManager(models.Model):

    # Relations
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self) -> str:
        return self.user.first_name + " : " + self.depot.name


class DepotCustomer(models.Model):

    customer = models.OneToOneField(Customer, on_delete=models.PROTECT)
    depot = models.ForeignKey(Depot, on_delete=models.PROTECT)
