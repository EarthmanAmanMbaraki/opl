from rest_framework.serializers import (
	ModelSerializer, 
	SerializerMethodField,	
	)

from . models import Entry

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without truncateing'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))
    
class EntryCreateSer(ModelSerializer):

    class Meta:
        model = Entry
        fields = [
            "id",
            "product",
            "truck",
            "entry_no",
            "order_no",
            "date",
            "vol_obs",
            "vol_20",
            "selling_price",
        ]

class EntryListSer(ModelSerializer):
    customer = SerializerMethodField()
    product = SerializerMethodField()
    depot = SerializerMethodField()
    truck = SerializerMethodField()
    product_id = SerializerMethodField()
    class Meta:
        model = Entry
        fields = [
            "id",
            "product",
            "product_id",
            "customer",
            "entry_no",
            "order_no",
            "date",
            "vol_obs",
            "vol_20",
            "selling_price",
            "depot",
            "truck",
        ]

    def get_product(self, obj):
        return obj.product.product.name
    def get_customer(self, obj):
        return obj.truck.customer.name
    def get_depot(self, obj):
        return obj.product.depot.name
    def get_truck(self, obj):
        return obj.truck.id
    def get_product_id(self, obj):
        return obj.product.id
