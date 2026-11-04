from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsAdminRole
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Expense
from .serializers import ExpenseSerializer
from datetime import timedelta

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']

    def get_queryset(self):
        qs = Expense.objects.filter(store=self.request.user.store)
        category = self.request.query_params.get('category')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if category:
            qs = qs.filter(category=category)
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        return qs

    def perform_create(self, serializer):
        from accounts.models import log_audit_event
        expense = serializer.save(
            store=self.request.user.store,
            user=self.request.user
        )
        log_audit_event(
            request=self.request,
            action='GASTO_REGISTRADO',
            entity=expense.title,
            entity_id=expense.id,
            description=f"Registró gasto '{expense.title}' por ${float(expense.amount):.2f} ({expense.get_category_display()})",
            before_data=None,
            after_data={'concepto': expense.title, 'monto': float(expense.amount), 'categoria': expense.get_category_display()}
        )

    def perform_destroy(self, instance):
        from accounts.models import log_audit_event
        log_audit_event(
            request=self.request,
            action='GASTO_ELIMINADO',
            entity=instance.title,
            entity_id=instance.id,
            description=f"Eliminó gasto '{instance.title}' de ${float(instance.amount):.2f}",
            before_data={'concepto': instance.title, 'monto': float(instance.amount), 'categoria': instance.get_category_display()},
            after_data=None
        )
        instance.delete()

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        store = request.user.store
        today = timezone.localdate()
        first_day_of_month = today.replace(day=1)

        # Gastos de hoy
        today_expenses = Expense.objects.filter(store=store, date=today).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )

        # Gastos del mes
        month_expenses = Expense.objects.filter(store=store, date__gte=first_day_of_month, date__lte=today).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )

        # Desglose por categoría en el mes
        by_category = Expense.objects.filter(
            store=store,
            date__gte=first_day_of_month,
            date__lte=today
        ).values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        category_dict = dict(Expense.CATEGORY_CHOICES)
        category_breakdown = [
            {
                "category": item['category'],
                "category_label": category_dict.get(item['category'], item['category']),
                "total": float(item['total'] or 0.0),
                "count": item['count']
            }
            for item in by_category
        ]

        return Response({
            "today_total": float(today_expenses['total'] or 0.0),
            "today_count": today_expenses['count'] or 0,
            "month_total": float(month_expenses['total'] or 0.0),
            "month_count": month_expenses['count'] or 0,
            "by_category": category_breakdown
        }, status=status.HTTP_200_OK)
