from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages

from .models import Payment, Transaction
from apps.courses.models import Course


# ─── Permission Helper ────────────────────────────────────────────────────────

def get_student(user):
    try:
        return user.student_profile
    except Exception:
        return None


# ─── Checkout Views ───────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class CheckoutView(View):
    """
    GET  /payments/checkout/<int:course_id>/  — shows checkout page
    POST /payments/checkout/<int:course_id>/  — initiates payment
    """
    def get(self, request, course_id):
        if request.user.role != 'student':
            messages.error(request, 'Only students can purchase courses.')
            return redirect('course_detail', pk=course_id)

        student = get_student(request.user)
        course  = get_object_or_404(Course, pk=course_id, is_published=True)

        # Already purchased
        if Payment.objects.filter(
            student=student, course=course, status='completed'
        ).exists():
            messages.info(request, 'You have already purchased this course.')
            return redirect('my_enrollments')

        # Already enrolled (free course)
        from apps.interactions.models import Enrollment
        if Enrollment.objects.filter(student=student, course=course).exists():
            messages.info(request, 'You are already enrolled in this course.')
            return redirect('my_enrollments')

        effective_price = course.discount_price if course.discount_price else course.price

        return render(request, 'payments/checkout.html', {
            'course':          course,
            'effective_price': effective_price,
        })

    def post(self, request, course_id):
        if request.user.role != 'student':
            return redirect('landing')

        student = get_student(request.user)
        course  = get_object_or_404(Course, pk=course_id, is_published=True)

        # Handle free courses — enroll directly
        if course.is_free:
            payment = Payment.objects.create(
                student=student,
                course=course,
                amount=0.00,
                currency='INR',
                gateway='free',
                status='completed',
            )
            payment.mark_completed()
            messages.success(request, f'You are now enrolled in {course.title}!')
            return redirect('payment_success', payment_id=payment.pk)

        # Paid course — create pending payment
        effective_price = course.discount_price if course.discount_price else course.price
        payment = Payment.objects.create(
            student=student,
            course=course,
            amount=effective_price,
            currency='INR',
            gateway=request.POST.get('gateway', 'razorpay'),
            coupon_code=request.POST.get('coupon_code', ''),
            status='pending',
        )

        # In production: call Razorpay/Stripe API here
        # For now we simulate a successful payment
        payment.mark_completed()
        messages.success(request, 'Payment successful! You are now enrolled.')
        return redirect('payment_success', payment_id=payment.pk)


@method_decorator(login_required, name='dispatch')
class PaymentSuccessView(View):
    """
    GET /payments/success/<int:payment_id>/
    Shows the payment success page after enrollment.
    """
    def get(self, request, payment_id):
        student = get_student(request.user)
        payment = get_object_or_404(Payment, pk=payment_id, student=student)
        return render(request, 'payments/success.html', {
            'payment': payment,
            'course':  payment.course,
        })


@method_decorator(login_required, name='dispatch')
class PaymentFailedView(View):
    """
    GET /payments/failed/<int:payment_id>/
    Shows the payment failed page.
    """
    def get(self, request, payment_id):
        student = get_student(request.user)
        payment = get_object_or_404(Payment, pk=payment_id, student=student)
        return render(request, 'payments/failed.html', {
            'payment': payment,
            'course':  payment.course,
        })


@method_decorator(login_required, name='dispatch')
class MyPaymentsView(View):
    """
    GET /payments/history/
    Shows full payment history for the logged-in student.
    """
    def get(self, request):
        if request.user.role != 'student':
            messages.error(request, 'Access denied.')
            return redirect('landing')
        student  = get_student(request.user)
        payments = Payment.objects.filter(
            student=student
        ).select_related('course').order_by('-created_at')
        return render(request, 'payments/history.html', {
            'payments': payments,
        })


@method_decorator(login_required, name='dispatch')
class PaymentDetailView(View):
    """
    GET /payments/<int:payment_id>/
    Shows details of a single payment including transactions.
    """
    def get(self, request, payment_id):
        if request.user.role != 'student':
            messages.error(request, 'Access denied.')
            return redirect('landing')
        student      = get_student(request.user)
        payment      = get_object_or_404(Payment, pk=payment_id, student=student)
        transactions = payment.transactions.all().order_by('-created_at')
        return render(request, 'payments/detail.html', {
            'payment':      payment,
            'transactions': transactions,
        })


@method_decorator(login_required, name='dispatch')
class RefundRequestView(View):
    """
    POST /payments/<int:payment_id>/refund/
    Student requests a refund for a completed payment.
    """
    def post(self, request, payment_id):
        if request.user.role != 'student':
            return redirect('landing')
        student = get_student(request.user)
        payment = get_object_or_404(
            Payment, pk=payment_id,
            student=student, status='completed'
        )

        # Log the refund transaction
        Transaction.objects.create(
            payment=payment,
            gateway_tx_id=f'refund_{payment_id}',
            gateway_status='refunded',
            raw_response={'note': 'Refund requested by student'},
            amount=payment.amount,
            currency=payment.currency,
            is_refund=True,
        )
        payment.status = 'refunded'
        payment.save(update_fields=['status'])
        messages.success(request, 'Refund request submitted successfully.')
        return redirect('my_payments')