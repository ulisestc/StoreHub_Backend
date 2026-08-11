from django.http import JsonResponse
from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint de salud para verificar el estado de la API y la conexión a la base de datos.
    """
    db_ok = False
    db_error = None
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception as e:
        db_error = str(e)

    status_code = 200 if db_ok else 503
    data = {
        "status": "healthy" if db_ok else "unhealthy",
        "database": {
            "status": "connected" if db_ok else "disconnected",
            "error": db_error
        },
        "timestamp": timezone.now().isoformat(),
        "service": "StoreHub Backend API",
        "version": "1.0.0",
        "institution": "FCC BUAP 2036"
    }
    return JsonResponse(data, status=status_code)
