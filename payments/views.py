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

    if created:
        # Process newly created payment
        if random.choice([True, False]):
            payment.status = Payment.Status.SUCCESS
        else:
            payment.status = Payment.Status.FAILED

        payment.save()

        return Response({
            "message": "Payment processed",
            "transaction_id": payment.transaction_id,
            "status": payment.status,
            "retry_count": payment.retry_count
        }, status=status.HTTP_201_CREATED)

    if not created:
        # If already SUCCESS or FAILED → no retry allowed
        if payment.status in [Payment.Status.SUCCESS, Payment.Status.FAILED]:
            return Response({
                "message": "Duplicate request - terminal state reached",
                "transaction_id": payment.transaction_id,
                "status": payment.status,
                "retry_count": payment.retry_count
            })

        # If still PENDING → retry
        if payment.retry_count < 3:
            payment.retry_count += 1

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

        # Safety fallback
        return Response({
            "message": "Duplicate request",
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
