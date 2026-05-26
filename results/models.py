from django.db import models
from django.conf import settings
from exams.models import Exam

class Result(models.Model):
    """
    Result Model: Core transactional record of a completed examination.
    Stores the final computed metric score dynamically derived from 
    both positive correct answers and algorithms enforcing negative marking.
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'is_student': True})
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    
    score = models.FloatField(default=0.0)
    proctoring_violations = models.PositiveIntegerField(default=0, help_text="Count of detected security violations (tab switching, etc.)")
    
    attempt_number = models.PositiveIntegerField(default=1)
    # Automatically timestamped when the test submission completes.
    completed_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def correct_answers_count(self):
        return self.answers.filter(selected_choice__is_correct=True).count()

    @property
    def wrong_answers_count(self):
        # We define 'wrong' as having selected a choice that is NOT correct
        # This excludes unattempted (where selected_choice is null)
        return self.answers.filter(selected_choice__isnull=False, selected_choice__is_correct=False).count()

    @property
    def unattempted_count(self):
        return self.answers.filter(selected_choice__isnull=True).count()

    @property
    def total_questions_count(self):
        return self.answers.count()
    
    @property
    def attempt_total_marks(self):
        from django.db.models import Sum
        total = self.answers.aggregate(total_m=Sum('question__marks'))['total_m']
        return total if total is not None else self.exam.total_marks

    @property
    def is_pass(self):
        return self.score >= (self.attempt_total_marks / 2)
    
    class Meta:
        # We allow up to 2 attempts (managed in views), so we remove the strict unique constraint.
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.student.username} - {self.exam.title} - Score: {self.score}/{self.exam.total_marks}"

class StudentAnswer(models.Model):
    """
    Stores the student's selected choice for each question in an exam.
    """
    result = models.ForeignKey(Result, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey('exams.Question', on_delete=models.CASCADE)
    selected_choice = models.ForeignKey('exams.Choice', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.result.student.username} - {self.question.text[:20]}"
