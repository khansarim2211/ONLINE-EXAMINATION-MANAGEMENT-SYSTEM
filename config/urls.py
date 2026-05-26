"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render

from exams.models import Exam, Course
from results.models import Result
from django.utils import timezone
import json

def dynamic_home(request):
    context = {}
    if request.user.is_authenticated:
        if getattr(request.user, 'is_student', False):
            # --- STUDENT DASHBOARD LOGIC ---
            taken_results = Result.objects.filter(student=request.user)
            completed_exam_ids = []
            attempt_counts = {}
            for res in taken_results:
                exam_id = res.exam.id
                if res.is_pass:
                    completed_exam_ids.append(exam_id)
                else:
                    attempt_counts[exam_id] = res.attempt_number
                    if res.attempt_number >= 2 or not res.exam.allow_reattempt:
                        completed_exam_ids.append(exam_id)
            
            available_exams = Exam.objects.exclude(id__in=completed_exam_ids)
            
            if request.user.department:
                from django.db.models import Q
                available_exams = available_exams.filter(Q(department=request.user.department) | Q(department__isnull=True))
            
            selected_course_id = request.GET.get('course_id')
            if selected_course_id:
                available_exams = available_exams.filter(course_id=selected_course_id)

            now = timezone.now()
            active_list = []
            upcoming_list = []
            
            for e in available_exams:
                attempts = attempt_counts.get(e.id, 0)
                e.is_reattempt = attempts > 0
                
                if not e.scheduled_date or e.scheduled_date <= now:
                    active_list.append(e)
                else:
                    upcoming_list.append(e)

            active_list.sort(key=lambda x: x.scheduled_date if x.scheduled_date else now, reverse=True)
            context['active_exams'] = active_list
            
            # Sort upcoming exams by soonest start
            upcoming_list.sort(key=lambda x: x.scheduled_date)
            context['upcoming_exams'] = upcoming_list
            
            past_results = Result.objects.filter(student=request.user).order_by('-completed_at')
            enriched_results = []
            total_percentage_sum = 0
            passed_count = 0
            
            passed_exam_ids = {r.exam.id for r in past_results if r.is_pass}
            
            for res in past_results:
                res.percentage = round((res.score / res.attempt_total_marks) * 100, 2) if res.attempt_total_marks > 0 else 0
                res.exam_passed_overall = res.exam.id in passed_exam_ids
                res.color = '#38a169' if res.is_pass or res.exam_passed_overall else '#e53e3e'
                enriched_results.append(res)
                total_percentage_sum += res.percentage
                if res.is_pass: passed_count += 1
            
            # Improved Subject Discovery: Show courses from student's department OR courses that have available exams
            course_ids_from_exams = available_exams.values_list('course_id', flat=True).distinct()
            
            if request.user.department:
                # If user has a department, show their curriculum
                student_courses = Course.objects.filter(department=request.user.department)
                if request.user.semester:
                    student_courses = student_courses.filter(semester=request.user.semester)
                
                # Also include any other courses that have active exams for them (e.g. cross-dept electives)
                student_courses = (student_courses | Course.objects.filter(id__in=course_ids_from_exams)).distinct()
            else:
                # Fallback for new users: just show courses that have available exams
                student_courses = Course.objects.filter(id__in=course_ids_from_exams)

            
            total_score_sum = sum(res.score for res in past_results)
            total_max_sum = sum(res.attempt_total_marks for res in past_results)
            
            context.update({
                'past_results': enriched_results,
                'kpi_total_attempted': past_results.count(),
                'kpi_passed_count': passed_count,
                'kpi_avg_score': round(total_percentage_sum / past_results.count(), 2) if past_results.exists() else 0,
                'kpi_avg_raw': round(total_score_sum / past_results.count(), 1) if past_results.exists() else 0,
                'kpi_max_avg': round(total_max_sum / past_results.count(), 1) if past_results.exists() else 0,
                'student_courses': student_courses,
                'selected_course_id': int(selected_course_id) if selected_course_id else None,
            })
        elif getattr(request.user, 'is_teacher', False):
            return redirect('teacher_dashboard')
            
    return render(request, 'home.html', context)

# --- ADMIN BRANDING ---
from django.contrib import admin
from . import admin_custom
admin.site.site_header = "Examify Administration"

admin.site.site_title = "Examify Control Center"
admin.site.index_title = "System Management Hub"

urlpatterns = [
    path('admin/', admin.site.urls),
    # Accounts app URLs for login, register, etc.
    path('accounts/', include('accounts.urls')),
    # Exams app URLs
    path('exams/', include('exams.urls')),
    # Payments app URLs
    path('payments/', include('payments.urls')),
    # Home page dashboard
    path('', dynamic_home, name='home'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
