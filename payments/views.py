from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from exams.models import Exam
from .models import Payment
import uuid

@login_required
def initiate_payment(request, exam_id):
    """
    Displays the premium checkout page for a re-attempt.
    """
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Check if student is actually eligible for re-attempt
    from results.models import Result
    past_attempts = Result.objects.filter(student=request.user, exam=exam).count()
    
    if past_attempts == 0:
        messages.error(request, "First attempt is free! No payment needed.")
        return redirect('take_exam', pk=exam.id)
    
    if past_attempts >= 2:
        messages.error(request, "Maximum attempts reached.")
        return redirect('student_dashboard')

    # Check if already paid
    if Payment.objects.filter(student=request.user, exam=exam, status='completed').exists():
        return redirect('take_exam', pk=exam.id)

    return render(request, 'payments/checkout.html', {
        'exam': exam,
        'amount': 500.00
    })

@login_required
def process_payment(request, exam_id):
    """
    Mock payment processing. In a real scenario, this would be a webhook 
    or a callback from Razorpay/Stripe.
    """
    if request.method == 'POST':
        exam = get_object_or_404(Exam, id=exam_id)
        
        # Simulate payment success
        payment, created = Payment.objects.get_or_create(
            student=request.user,
            exam=exam,
            defaults={'amount': 500.00, 'status': 'completed', 'transaction_id': f"TXN-{uuid.uuid4().hex[:8].upper()}"}
        )
        
        if not created:
            payment.status = 'completed'
            payment.transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
            payment.save()
            
        messages.success(request, f"Payment successful! You can now re-attempt {exam.title}.")
        return redirect('take_exam', pk=exam.id)
        
    return redirect('student_dashboard')
