from django.http import HttpResponse, JsonResponse
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


def swagger_ui(request):
    """
    Interfaz interactiva Swagger UI para la documentación de OpenAPI.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>StoreHub API - Swagger UI</title>
        <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.18.3/swagger-ui.min.css" />
        <link rel="icon" type="image/png" href="https://swagger.io/favicon-32x32.png" sizes="32x32" />
        <style>
            html { box-sizing: border-box; overflow-y: scroll; }
            *, *:before, *:after { box-sizing: inherit; }
            body { margin: 0; background: #fafafa; font-family: sans-serif; }
            .topbar { background-color: #1a202c; padding: 10px 0; }
            .topbar-wrapper { display: flex; align-items: center; max-width: 1460px; margin: 0 auto; padding: 0 20px; }
            .topbar-title { color: #ffffff; font-size: 20px; font-weight: bold; text-decoration: none; }
            .topbar-subtitle { color: #a0aec0; font-size: 14px; margin-left: 15px; }
        </style>
    </head>
    <body>
        <div class="topbar">
            <div class="topbar-wrapper">
                <span class="topbar-title">🏬 StoreHub API Docs</span>
                <span class="topbar-subtitle">Facultad de Ciencias de la Computación BUAP 2036</span>
            </div>
        </div>
        <div id="swagger-ui"></div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.18.3/swagger-ui-bundle.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.18.3/swagger-ui-standalone-preset.js"></script>
        <script>
        window.onload = function() {
          const ui = SwaggerUIBundle({
            url: "/api/schema/",
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            plugins: [
              SwaggerUIBundle.plugins.DownloadUrl
            ],
            layout: "BaseLayout"
          });
          window.ui = ui;
        };
        </script>
    </body>
    </html>
    """
    return HttpResponse(html_content)
