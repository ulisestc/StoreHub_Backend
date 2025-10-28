
## Plan de Implementación de Vistas

| Aplicación | Enfoque Recomendado | Pasos a Seguir |
| :--- | :--- | :--- |
| **`accounts `** | `djoser` + `simplejwt` | 1. Instalar y configurar `djoser` y `djangorestframework-simplejwt`.<br>2. `djoser` proveerá los endpoints para registro (`/users/`), gestión de perfil (`/users/me/`), etc.<br>3. `simplejwt` proveerá los endpoints para obtener/refrescar tokens (`/token/`).<br>4. `djoser` se encarga de la lógica segura, como hashear contraseñas al registrar. |
| **`products ✅`** | `ModelViewSet` + Permisos | 1. Usar `ModelViewSet` para un CRUD rápido.<br>2. **Añadir `permission_classes = [IsAuthenticated]`** para requerir un token JWT válido en todas las peticiones.<br>3. Opcional: Usar permisos más granulares (ej. `IsAdminUser`) para acciones como `update` o `delete`. |
| **`clients ✅`** | `ModelViewSet` + Permisos | 1. Usar `ModelViewSet` para un CRUD rápido.<br>2. **Añadir `permission_classes = [IsAuthenticated]`** para asegurar que solo usuarios autenticados puedan gestionar clientes. |
| **`sales ✅`** | `ViewSet` personalizado + Permisos | 1. Crear un `ViewSet` que no herede de `ModelViewSet` o una `APIView`.<br>2. **Añadir `permission_classes = [IsAuthenticated]`**.<br>3. Sobrescribir el método `create()` para implementar la lógica de negocio dentro de una `transaction.atomic()`: crear la venta, sus detalles y actualizar el stock de los productos. |
| **`inventory ✅`** | `ViewSet` personalizado + Permisos | 1. Crear un `ViewSet` (ej. `CreateModelMixin`, `ListModelMixin`).<br>2. **Añadir `permission_classes = [IsAdminUser]`** para que solo administradores puedan registrar movimientos de inventario.<br>3. Sobrescribir el método `perform_create()` para actualizar el `stock` del producto asociado después de crear el movimiento. |

## Plan de Implementación de Serializadores

| Aplicación | Tipo de Serializador | Razón |
| :--- | :--- | :--- |
| **`products ✅`** | `ModelSerializer` estándar | CRUD simple, sin lógica de negocio compleja en el serializador. |
| **`clients ✅`** | `ModelSerializer` estándar | CRUD simple, sin lógica de negocio compleja en el serializador. |
| **`accounts `** | Serializadores de `djoser` o personalizados | Para manejar de forma segura la creación de usuarios (hashear contraseñas) y controlar los campos expuestos. |
| **`sales ✅ `** | `ModelSerializer` con anidación y `create()` personalizado | Para manejar la creación de objetos relacionados (detalles de venta) y la lógica de negocio en una sola transacción. |
| **`inventory ✅`** | `ModelSerializer` estándar | La lógica de negocio principal (actualizar stock) se delega a la vista (`perform_create`), el serializador solo valida los datos. |


Para empezar, necesitarás instalar estas librerías:

```bash
pip install djangorestframework-simplejwt djoser
```

Luego, deberás configurar `djangorestframework-simplejwt` y `djoser` en tu archivo `settings.py`.

TODO

1. Arreglar superusuario (Modelo de accounts) ✅ ✅ (Manager personalizado) 
2. Probar endpoints de products, categories (Ahora que hay auth) ✅ ✅ 
3. Probar endopoints de clients ✅ ✅ 
4. Crear las vistas y logica de negocio de sales e inventory ✅ ✅ 
5. Crear la aplicación de reportes ✅ ✅ 
6. Crear reporte de low stock ✅ ✅ 
7. Agregar paginación global ✅ ✅ 
8. Busqueda por nombre, código y categoría en productos ✅ ✅ 
9. Verificar si existen / nos sirven los endpoints de djoser para accounts

storehub@gmail.com
storehubpassword

https://gemini.google.com/share/4433bde9b6f7