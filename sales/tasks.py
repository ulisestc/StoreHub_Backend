from django.core.mail import send_mail
from django.conf import settings
from .models import SaleDetail, Sale
from celery import shared_task

@shared_task
def send_ticket_email(sale_id, email_to=None):
    """
    Envía el ticket de compra por correo.
    Si email_to no se proporciona, intenta usar el correo del cliente asociado a la venta.
    """
    try:
        sale = Sale.objects.get(id=sale_id)
    except Sale.DoesNotExist:
        return False, "La venta no existe."

    recipient_email = email_to or (sale.client.email if sale.client else None)
    
    if not recipient_email:
        return False, "No se proporcionó un correo electrónico."
        
    store_name = sale.store.name if sale.store else "Nuestra Tienda"
    asunto = f"Tu Ticket de Compra en {store_name} - Venta #{sale.id}"
    
    # Obtener detalles
    details = sale.details.all()
    
    detalles_texto = ""
    for detail in details:
        detalles_texto += f"- {detail.quantity}x {detail.product.name} = ${detail.quantity * detail.price_at_sale}\n"
    
    cliente_nombre = sale.client.name if sale.client else "Cliente"
    
    mensaje = (
        f"¡Hola {cliente_nombre}!\n\n"
        f"Gracias por tu compra. Aquí tienes el resumen de tu ticket:\n\n"
        f"{detalles_texto}\n"
        f"Subtotal: ${sale.subtotal}\n"
        f"Impuestos (IVA): ${sale.impuestos}\n"
        f"Total Pagado: ${sale.total}\n\n"
        f"¡Esperamos verte pronto!\n"
    )
    
    try:
        send_mail(
            asunto,
            mensaje,
            settings.EMAIL_HOST_USER,
            [recipient_email],
            fail_silently=False,
        )
        return True, "Correo enviado correctamente."
    except Exception as mail_error:
        print(f"No se pudo enviar el correo: {mail_error}")
        return False, str(mail_error)
