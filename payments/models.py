from django.db import models

class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"

    transaction_id = models.CharField(
        max_length=100,
        unique=True,   # 🔥 critical for idempotency
        db_index=True
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    retry_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"