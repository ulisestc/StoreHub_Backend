
from django.db import migrations
from django.contrib.auth import get_user_model

def create_superuser(apps, schema_editor):
    User = get_user_model()
    
    ADMIN_EMAIL = "storehub@gmail.com"
    ADMIN_PASSWORD = "storehubpassword" 
    # --------------------------------

    if not User.objects.filter(email=ADMIN_EMAIL).exists():
        print(f"Creando superusuario {ADMIN_EMAIL}...")
        
        # Llama al manager personalizado
        User.objects.create_superuser(
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            first_name="Admin",
            last_name="StoreHub",
            role="admin" )
    else:
        print(f"El superusuario {ADMIN_EMAIL} ya existe. No se hace nada.")

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'), 
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]