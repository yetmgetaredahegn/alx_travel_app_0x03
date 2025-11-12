from rest_framework import viewsets,status
from django.views.decorators.csrf import csrf_exempt
from .models import Listing, Booking
from .serializers import ListingSerializer, BookingSerializer

import uuid
import hmac
import hashlib
import json
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import send_mail
from .models import Booking, Payment
from .tasks import send_booking_confirmation_email, send_payment_confirmation_email  # Optional Celery

class ListingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Listings.
    Provides list, create, retrieve, update, delete.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Bookings.
    Provides list, create, retrieve, update, delete.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()

        # Trigger email asynchronously
        send_booking_confirmation_email.delay(booking.id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)



@api_view(["POST"])
def initiate_payment(request):
    """
    Initiate Chapa payment for a booking.
    """
    data = request.data
    booking_id = data.get("booking_id")
    amount = data.get("amount")
    currency = data.get("currency", "ETB")

    if not booking_id or not amount:
        return Response({"error": "booking_id and amount are required"}, status=400)

    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=404)

    tx_ref = str(uuid.uuid4())

    # Create Payment record with status pending
    payment = Payment.objects.create(
        booking=booking,
        tx_ref=tx_ref,
        amount=amount,
        currency=currency
    )

    payload = {
        "amount": str(amount),
        "currency": currency,
        "email": booking.user.email,
        "first_name": booking.user.get_full_name().split()[0],
        "last_name": booking.user.get_full_name().split()[-1],
        "tx_ref": tx_ref,
        "callback_url": settings.PAYMENT_CALLBACK_URL,
        "return_url": settings.PAYMENT_RETURN_URL,
        "customization[title]": "Travel Booking Payment",
        "customization[description]": f"Payment for booking {booking.trip_name}",
    }

    headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
    response = requests.post(f"{settings.CHAPA_BASE_URL}/transaction/initialize", headers=headers, data=payload)

    if response.status_code != 200:
        payment.mark_failed()
        return Response({"error": "Failed to initialize payment", "details": response.text}, status=400)

    checkout_url = response.json()["data"]["checkout_url"]

    return Response({"checkout_url": checkout_url, "tx_ref": tx_ref}, status=200)


@csrf_exempt
@api_view(["POST"])
def chapa_webhook(request):
    """
    Chapa webhook to confirm payment.
    """
    # Verify HMAC signature
    signature = request.headers.get("chapa-signature")
    if not signature:
        return Response({"detail": "Missing signature"}, status=400)

    computed_signature = hmac.new(
        settings.CHAPA_SECRET_KEY.encode(),
        msg=request.body,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, computed_signature):
        return Response({"detail": "Invalid signature"}, status=403)

    # Parse flat payload
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return Response({"detail": "Invalid JSON"}, status=400)

    tx_ref = payload.get("tx_ref")
    status = payload.get("status")
    email = payload.get("email")
    amount = payload.get("amount")

    if not tx_ref:
        return Response({"detail": "tx_ref not provided"}, status=400)

    try:
        payment = Payment.objects.get(tx_ref=tx_ref)
    except Payment.DoesNotExist:
        return Response({"detail": "Payment not found"}, status=404)

    # Update payment based on Chapa status
    if status == "success" and payment.status != "completed":
        payment.mark_completed()
        # Send confirmation email
        if email:
            send_payment_confirmation_email.delay(email, str(amount), tx_ref)
            # Or direct send_mail if no Celery:
            # send_mail(
            #     subject="Payment Successful",
            #     message=f"Hello, your payment of {amount} {payment.currency} was successful. TxRef: {tx_ref}",
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=[email],
            #     fail_silently=True,
            # )
    elif status == "failed" and payment.status != "failed":
        payment.mark_failed()

    return Response({"detail": "Webhook processed successfully"}, status=200)
