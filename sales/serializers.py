from dataclasses import fields
from itertools import product
from typing import Dict
from rest_framework.serializers import (
	ModelSerializer, 
	SerializerMethodField,	
	)

from customer.serializers import RetrieveCustomerSer, RetrieveTruckSer
from depot.serializers import RetrieveDepotSer
from product.serializers import RetrieveProductSer

from . models import Sale

class CreateSaleSer(ModelSerializer):

    class Meta:
        model = Sale
        fields = [
            "customer",
            "depot",
            "product",
            "truck",
            "entry_no",
            "date",
            "is_paid",
            "is_loaded",
            "lpo_no",
            "order_no",
            "selling_price",
            "vol_obs",
            "vol_20",
        ]

class RetrieveSaleSer(ModelSerializer):
    customer = SerializerMethodField()
    depot = SerializerMethodField()
    product = SerializerMethodField()
    truck = SerializerMethodField()
    class Meta:
        model = Sale
        fields = [
            "customer",
            "depot",
            "product",
            "truck",
            "entry_no",
            "date",
            "is_paid",
            "is_loaded",
            "lpo_no",
            "order_no",
            "selling_price",
            "vol_obs",
            "vol_20",
        ]
    
    def get_customer(self, obj) -> Dict:
        return RetrieveCustomerSer(obj.customer).data
    
    def get_depot(self, obj) -> Dict:
        return RetrieveDepotSer(obj.depot).data

    def get_product(self, obj) -> Dict:
        return RetrieveProductSer(obj.product).data
    
    def get_truck(self, obj) -> Dict:
        return RetrieveTruckSer(obj.truck).data