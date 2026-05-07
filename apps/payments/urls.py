# ── urls.py ───────────────────────────────────────────────────────────────────
# Paste this into apps/payments/urls.py

from django.urls import path
from .views import (
    CheckoutView,
    PaymentSuccessView,
    PaymentFailedView,
    MyPaymentsView,
    PaymentDetailView,
    RefundRequestView,
)

urlpatterns = [
    path('checkout/<int:course_id>/',       CheckoutView.as_view(),         name='checkout'),
    path('success/<int:payment_id>/',       PaymentSuccessView.as_view(),   name='payment_success'),
    path('failed/<int:payment_id>/',        PaymentFailedView.as_view(),    name='payment_failed'),
    path('history/',                        MyPaymentsView.as_view(),       name='my_payments'),
    path('<int:payment_id>/',               PaymentDetailView.as_view(),    name='payment_detail'),
    path('<int:payment_id>/refund/',        RefundRequestView.as_view(),    name='refund_request'),
]