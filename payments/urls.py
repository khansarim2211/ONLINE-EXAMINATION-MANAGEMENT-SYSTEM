from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<int:exam_id>/', views.initiate_payment, name='initiate_payment'),
    path('process/<int:exam_id>/', views.process_payment, name='process_payment'),
]
