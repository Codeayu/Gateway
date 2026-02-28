from django.urls import path
from .views import create_payment, get_payment

urlpatterns = [
    path("payments/", create_payment, name="create_payment"),
    path("payments/<str:transaction_id>/", get_payment, name="get_payment"),
]