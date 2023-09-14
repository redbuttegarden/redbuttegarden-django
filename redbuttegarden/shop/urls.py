from django.urls import path

from . import views

app_name = 'shop'
urlpatterns = [
    path('payment-methods', views.payment_methods, name='payment-methods'),
    path('snipcart-webhook', views.snipcart_webhook, name='snipcart-webhook'),
    path('checkout', views.checkout, name='shop-checkout'),
]