from django.urls import path
from . import views

urlpatterns = [
    # Teacher URLs
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/exam/new/', views.ExamCreateView.as_view(), name='create_exam'),
    path('teacher/exam/<int:pk>/', views.exam_detail, name='exam_detail'),
    path('teacher/exam/<int:pk>/edit/', views.ExamUpdateView.as_view(), name='edit_exam'),
    path('teacher/exam/<int:pk>/add_question/', views.add_question, name='add_question'),
    path('teacher/exam/<int:pk>/bulk_add_questions/', views.bulk_add_questions, name='bulk_add_questions'),
    path('teacher/question/<int:pk>/edit/', views.edit_question, name='edit_question'),
    path('teacher/question/<int:pk>/delete/', views.delete_question, name='delete_question'),
    path('teacher/exam/<int:pk>/results/', views.view_exam_results, name='view_exam_results'),
    path('teacher/exam/<int:pk>/delete_exam/', views.delete_exam, name='delete_exam'),
    path('teacher/analytics/', views.teacher_analytics_overview, name='teacher_analytics_overview'),
    
    # Student URLs
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/exam/<int:pk>/take/', views.take_exam, name='take_exam'),
    path('student/result/<int:pk>/answers/', views.view_answer_sheet, name='view_answer_sheet'),
    path('student/result/<int:pk>/download/', views.download_result_pdf, name='download_result_pdf'),
    path('student/analytics/', views.student_analytics, name='student_analytics'),
]
