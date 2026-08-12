# Storehub Backend

REST API (SaaS Multitenant) desarrollada en Django 4.2 para el proyecto de Desarrollo de Sitios Web de la Benemérita Universidad Autónoma de Puebla.

Maestro: Luis Yael Méndez Sánchez.

## Autores
- [Ulises Torres](https://www.github.com/ulisestc)
- [Alfredo Escudero](https://github.com/AlfredoRiveraaa)
- [Yuri Martínez](https://github.com/JohanYuri)
- [Joselyn Ramírez](https://github.com/josramirez29)

## Tecnologías empleadas
- Django REST Framework (DRF)
- MySQL
- Arquitectura SaaS Multitenant (Una base de datos compartida, información aislada por tienda)
- Autenticación: Djoser + SimpleJWT (Tokens JWT)
- Pruebas Automatizadas: Django Test y Postman CLI (Newman)
- Documentación OpenAPI automática (drf-spectacular)

---

## Guía de Instalación y Uso

El proyecto se encuentra contenerizado con Docker para garantizar consistencia entre los entornos de desarrollo. No es necesaria la instalación local de Python o MySQL.

### 1. Requisitos Previos
- Docker y Docker Compose.
- Git.

### 2. Clonación y Configuración
Clonar el repositorio y acceder al directorio:
```bash
git clone <URL_DEL_REPO>
cd StoreHub_Backend
```

Crear el archivo de variables de entorno a partir de la plantilla:
- Windows (CMD): `copy .env.example .env`
- Mac/Linux: `cp .env.example .env`

Nota: En el archivo `.env` se puede configurar la variable `FRONTEND_DOMAIN` si el cliente de Angular utiliza un puerto distinto al 4200.

### 3. Ejecución del Proyecto
Para inicializar los servicios, ejecutar:
```bash
docker compose up --build
```

Una vez que los contenedores estén activos:
- La API estará disponible en: `http://localhost:8000/api/`
- El cliente local de pruebas para envío de correos (SMTP4Dev) en: `http://localhost:5000`

### 4. Población de la Base de Datos
Para generar datos iniciales de prueba (tiendas, usuarios, productos y ventas), se provee un script automatizado. Con los contenedores en ejecución, correr:
```bash
docker compose exec backend python manage.py seed_data
```

Credenciales generadas por defecto:
- Administrador: `admin@storehub.com` / `admin12345`
- Cajero: `vendedor@storehub.com` / `seller12345`

### 5. Documentación de la API
La documentación interactiva de los endpoints generada mediante Swagger se encuentra en:
[http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## Comandos Útiles

Aplicar migraciones tras cambios en los modelos de la base de datos:
```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

Ejecutar las pruebas unitarias automatizadas:
```bash
docker compose exec backend python manage.py test
```

Restablecer completamente la base de datos y generar datos semilla desde cero:
```bash
docker compose down -v
docker compose up --build -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_data
```