from rest_framework import viewsets, filters
from .models import Client
from .serializers import ClientSerializer
from rest_framework.permissions import IsAuthenticated

class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'phone']

    def get_queryset(self):
        return Client.objects.filter(store=self.request.user.store).order_by('name')

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.store)