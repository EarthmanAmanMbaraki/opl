from django.db import models
from django.core.cache import cache


class Customer(models.Model):
    # Attributes
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        super(Customer, self).save(*args, **kwargs)
        cache.delete("customer")
        cache.delete("customer-{}".format(self.pk))

    def __str__(self) -> str:
        return self.code + " : " + self.name


class Driver(models.Model):

    # Attributes
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.first_name


class Truck(models.Model):

    # Relations
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True
    )
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True)

    # Attributes
    plate_no = models.CharField(max_length=20)
    is_hired = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.driver.__str__() + " : " + self.plate_no
