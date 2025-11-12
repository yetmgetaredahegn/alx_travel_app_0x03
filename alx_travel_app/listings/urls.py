from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, BookingViewSet, chapa_webhook, initiate_payment

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('api/', include(router.urls)),
    path('initiate_payment/', initiate_payment,name="initiate-payment"),
    path('webhook/', chapa_webhook,name="chapa-webhook"),
]
