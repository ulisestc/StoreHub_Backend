
from django.db import migrations
from django.contrib.auth import get_user_model

def create_superuser(apps, schema_editor):
    User = get_user_model()
    
    # --- ¡CAMBIA ESTOS VALORES! ---
    ADMIN_EMAIL = "storehub@gmail.com"
    ADMIN_PASSWORD = "storehubpassword" 
    # --------------------------------

    # Revisa si el usuario ya existe para no fallar en futuros deploys
    if not User.objects.filter(email=ADMIN_EMAIL).exists():
        print(f"Creando superusuario {ADMIN_EMAIL}...")
        
        # Llama al manager personalizado que ya tienes
        User.objects.create_superuser(
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            first_name="Admin",
            last_name="StoreHub",
            role="admin" # Tu manager asigna esto por defecto, pero lo ponemos para ser explícitos
        )
    else:
        print(f"El superusuario {ADMIN_EMAIL} ya existe. No se hace nada.")

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'), # Depende de la migración inicial de tu app 'accounts'
    ]

    operations = [
        # Ejecuta la función que acabamos de definir
        migrations.RunPython(create_superuser),
    ]