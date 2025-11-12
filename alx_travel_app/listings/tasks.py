from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_confirmation_email(self, email, amount, tx_ref):
    subject = "Payment Successful — ALX Travel"
    message = (
        f"Hello,\n\n"
        f"Your payment of {amount} ETB has been successfully received.\n"
        f"Transaction Ref: {tx_ref}\n\n"
        f"Thank you for booking with ALX Travel!"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)




@shared_task
def send_booking_confirmation_email(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return

    subject = f"Booking Confirmed! (ID: {booking.id})"
    message = f"Hello {booking.user.get_full_name()},\n\n" \
              f"Your booking with ID {booking.id} is confirmed.\n\n" \
              "Thank you for choosing Alx Travel!"
    recipient = [booking.user.email]

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient,
        fail_silently=False,
    )
