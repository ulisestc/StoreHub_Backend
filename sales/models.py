from django.db import models

class Sale(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True)
    store = models.ForeignKey('accounts.Store', on_delete=models.CASCADE, related_name='sales')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    impuestos = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class SaleDetail(models.Model):
    sale = models.ForeignKey(Sale, related_name='details', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)

class CashRegisterSession(models.Model):
    store = models.ForeignKey('accounts.Store', on_delete=models.CASCADE, related_name='cash_sessions')
    opened_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='opened_cash_sessions')
    closed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='closed_cash_sessions', blank=True)
    
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2)
    expected_closing_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_closing_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)

    @property
    def is_open(self):
        return self.closed_at is None

    @property
    def discrepancy(self):
        if self.actual_closing_balance is not None and self.expected_closing_balance is not None:
            return self.actual_closing_balance - self.expected_closing_balance
        return None