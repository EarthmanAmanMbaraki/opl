from django.test import TestCase
from customer.models import Customer

class CustomerTestCase(TestCase):
    def setUp(self) -> None:
        Customer.objects.create(code="code", name="customer")
        Customer.objects.create(code="code2", name="customer2")
    
    def test_customer_create(self):
        code = Customer.objects.get(name="customer")
        code2 = Customer.objects.get(name="customer2")
        self.assertEqual(code, "code")
        self.assertEqual(code2, "code2")
