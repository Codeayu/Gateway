import random
from django.db import IntegrityError, transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from .serializer import PaymentSerializer


@api_view(["POST"])
def create_payment(request):

    transaction_id = request.data.get("transaction_id")
    amount = request.data.get("amount")

    if not transaction_id or not amount:
        return Response(
            {"error": "transaction_id and amount are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            payment = Payment.objects.create(
                transaction_id=transaction_id,
                amount=amount
            )
            created = True

    except IntegrityError:
        payment = Payment.objects.get(transaction_id=transaction_id)
        created = False

    # If duplicate request → idempotent response
    if not created:
    # Allow retry only if payment is still pending
    if payment.status == Payment.Status.PENDING and payment.retry_count < 3:

        payment.retry_count += 1

        # Simulate provider again
        if random.choice([True, False]):
            payment.status = Payment.Status.SUCCESS
        elif payment.retry_count >= 3:
            payment.status = Payment.Status.FAILED

        payment.save()

        return Response({
            "message": "Retry attempt",
            "transaction_id": payment.transaction_id,
            "status": payment.status,
            "retry_count": payment.retry_count
        })

    # Terminal state → just return existing
    return Response({
        "message": "Duplicate request - returning existing record",
        "transaction_id": payment.transaction_id,
        "status": payment.status,
        "retry_count": payment.retry_count
    })
    

@api_view(["GET"])
def get_payment(request, transaction_id):
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)
    except Payment.DoesNotExist:
        return Response(
            {"error": "Payment not found"},
            status=status.HTTP_404_NOT_FOUND
        )
