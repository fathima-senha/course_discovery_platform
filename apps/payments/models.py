from django.db import models
from apps.accounts.models import StudentProfile
from apps.courses.models import Course


class Payment(models.Model):
    """
    Records a payment intent or completed payment from a student for a course.
    One payment record per student per course purchase attempt.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"
        CANCELLED = "cancelled", "Cancelled"

    class Gateway(models.TextChoices):
        RAZORPAY = "razorpay", "Razorpay"
        STRIPE = "stripe", "Stripe"
        PAYPAL = "paypal", "PayPal"
        FREE = "free", "Free (no charge)"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,  # Never delete payment records
        related_name="payments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    gateway = models.CharField(max_length=20, choices=Gateway.choices, default=Gateway.RAZORPAY)
    gateway_order_id = models.CharField(max_length=200, blank=True)  # Gateway-side order ID
    coupon_code = models.CharField(max_length=50, blank=True)
    discount_applied = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "status"]),
            models.Index(fields=["course", "status"]),
        ]

    def __str__(self):
        return f"Payment #{self.id} — {self.student.user.email} | {self.course.title} | {self.status}"

    def mark_completed(self):
        from django.utils import timezone
        self.status = self.Status.COMPLETED
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "paid_at"])
        # Auto-enroll the student on successful payment
        from interactions.models import Enrollment
        Enrollment.objects.get_or_create(
            student=self.student,
            course=self.course,
            defaults={"status": Enrollment.Status.ACTIVE},
        )


class Transaction(models.Model):
    """
    Low-level ledger entry from the payment gateway.
    One payment can have multiple transactions (e.g. initial charge + refund).
    Stores raw gateway response for audit and debugging.
    """

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    gateway_tx_id = models.CharField(max_length=200, unique=True)  # Gateway transaction ID
    gateway_status = models.CharField(max_length=50)
    raw_response = models.JSONField(default=dict)  # Full gateway payload stored for audit
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    is_refund = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transaction"
        ordering = ["-created_at"]

    def __str__(self):
        prefix = "Refund" if self.is_refund else "Charge"
        return f"{prefix} {self.gateway_tx_id} ({self.gateway_status})"