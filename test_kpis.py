import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User
from sales.models import Sale, CashRegisterSession
from django.test import RequestFactory
from reports.views import SalesByDateReport
from sales.views import CashRegisterSessionViewSet

user = User.objects.get(email='admin@storehub.com')
factory = RequestFactory()

# Test Sales by Date Report
req = factory.get('/api/reports/sales-by-date/')
req.user = user
view = SalesByDateReport.as_view()
response = view(req)
print("SalesByDateReport:", response.data)

# Test Cash Register Open
req_open = factory.post('/api/cash-register/open/', {'opening_balance': 500.00}, format='json')
req_open.user = user
view_open = CashRegisterSessionViewSet.as_view({'post': 'open_session'})
res_open = view_open(req_open)
print("CashRegister Open:", res_open.data)

# Test Cash Register Current
req_current = factory.get('/api/cash-register/current/')
req_current.user = user
view_current = CashRegisterSessionViewSet.as_view({'get': 'current_session'})
res_current = view_current(req_current)
print("CashRegister Current:", res_current.data)

# Test Cash Register Close
session_id = res_open.data['id']
req_close = factory.post(f'/api/cash-register/{session_id}/close/', {'actual_closing_balance': 500.00}, format='json')
req_close.user = user
view_close = CashRegisterSessionViewSet.as_view({'post': 'close_session'})
res_close = view_close(req_close, pk=session_id)
print("CashRegister Close:", res_close.data)

