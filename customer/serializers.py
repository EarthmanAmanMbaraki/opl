from dataclasses import fields
import datetime
from pyexpat import model
from django.utils import timezone
from rest_framework.serializers import (
	ModelSerializer, 
	SerializerMethodField,
	ValidationError,	
	)
from order.models import Entry


from . models import Customer, Truck

class CustomerCreateSer(ModelSerializer):
	
	class Meta:
		model = Customer
		fields = [
            "id",
			"depot",
			"name",
			"location",
		]

class CustomerListSer(ModelSerializer):
	trucks = SerializerMethodField()
	class Meta:
		model = Customer
		fields = [
			"id",
			"name",
			"location",
			"trucks",
		]
	def get_trucks(self, obj):
		return TruckCreateSer(obj.truck_set.all(), many=True).data
	


class TruckCreateSer(ModelSerializer):
    
    class Meta:
        model = Truck
        fields = [
            "id",
			"customer",
			"plate_no",
            "driver"
		]
        


class TruckListSer(ModelSerializer):
    customer = SerializerMethodField()
    class Meta:
        model = Truck
        fields = [
            "id",
			"customer",
			"plate_no",
            "driver"
		]
        
    def get_customer(self, obj):
        return obj.customer.name

