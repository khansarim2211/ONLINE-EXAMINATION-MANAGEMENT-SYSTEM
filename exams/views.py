"""
examify_project/exams/views.py

This module contains the core business logic and HTTP views for the Examify platform.
It handles user dashboards, dynamic exam creation (including the Fast Paste AI parser),
real-time examination taking, and automated result calculation featuring custom
negative marking algorithms.

Developed for structural efficiency and clean MVC design in Django.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
import random
import json
import io
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

from .models import Exam, Question, Choice, Course
from .forms import ExamForm
from results.models import Result

# --- TEACHER VIEWS ---

@login_required
def teacher_dashboard(request):
    """
    Renders the Teacher Analytics Dashboard.
    Validates Role-Based Access Control (RBAC) to ensure only teachers can access.
    Compiles Key Performance Indicators (KPIs) like total exams, student reach, 
    and dynamically packages JSON data for the Chart.js visual frontend.
    """
    if not getattr(request.user, 'is_teacher', False):
        messages.error(request, "Access denied. Only teachers can view this page.")
        return redirect('home')
    
    exams = Exam.objects.filter(teacher=request.user)
    total_exams = exams.count()
    
    # KPIs calculation aggregation
    results = Result.objects.filter(exam__in=exams)
    total_students = results.values('student').distinct().count()
    results_published = results.values('exam').distinct().count()
    
    now = timezone.now()
    enriched_exams = []
    for exam in exams:
        if exam.scheduled_date:
            if exam.scheduled_date > now:
                exam.status = 'Scheduled'
                exam.status_color = '#d69e2e' # Yellow/Orange
            else:
                exam.status = 'Active'
                exam.status_color = '#38a169' # Green
        else:
            exam.status = 'Active'
            exam.status_color = '#38a169'
        enriched_exams.append(exam)
    # Pass chart data to context (sorted by engagement)
    exam_stats = []
    for ex in enriched_exams:
        count = Result.objects.filter(exam=ex).count()
        exam_stats.append({'title': ex.title, 'count': count})
    
    exam_stats.sort(key=lambda x: x['count'], reverse=True)
    chart_labels = json.dumps([s['title'] for s in exam_stats[:5]])
    chart_data = json.dumps([s['count'] for s in exam_stats[:5]])
        
    context = {
        'teacher_exams': enriched_exams,
        'kpi_total_exams': total_exams,
        'kpi_total_students': total_students,
        'kpi_results_published': results_published,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'now': timezone.now(),
    }
    return render(request, 'exams/teacher_dashboard.html', context)

@login_required
def teacher_analytics_overview(request):
    """
    Dedicated view for teachers to choose an exam for analytics.
    """
    if not getattr(request.user, 'is_teacher', False):
        return redirect('home')
    
    exams = Exam.objects.filter(teacher=request.user)
    return render(request, 'exams/analytics_overview.html', {'exams': exams})

@method_decorator(login_required, name='dispatch')
class ExamCreateView(CreateView):
    """
    Class-Based View (CBV) to handle the creation of new Exam configuration objects.
    Automatically assigns the authenticated teacher and their associated department
    to the generated exam object to prevent cross-department security flaws.
    """
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        
    def form_valid(self, form):
        # We must make sure the teacher is attached to the newly created exam
        if not getattr(self.request.user, 'is_teacher', False):
            messages.error(self.request, "Access denied.")
            return redirect('home')
        form.instance.teacher = self.request.user
        form.instance.department = self.request.user.department
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse_lazy('exam_detail', kwargs={'pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class ExamUpdateView(UpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        # Only allow the teacher who created it to edit it
        return super().get_queryset().filter(teacher=self.request.user)
    
    def get_success_url(self):
        messages.success(self.request, "Exam updated successfully.")
        return reverse_lazy('exam_detail', kwargs={'pk': self.object.pk})

@login_required
def exam_detail(request, pk):
    exam = get_object_or_404(Exam, pk=pk, teacher=request.user)
    return render(request, 'exams/exam_detail.html', {'exam': exam})

@login_required
def add_question(request, pk):
    """
    Teacher adds a question and up to 4 choices for it.
    """
    exam = get_object_or_404(Exam, pk=pk, teacher=request.user)
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        marks = request.POST.get('marks', 1)
        explanation = request.POST.get('explanation', '')
        
        # Create Question
        question = Question.objects.create(exam=exam, text=question_text, marks=marks, explanation=explanation)
        
        # Create corresponding choices
        for i in range(1, 5):
            choice_text = request.POST.get(f'choice_{i}')
            # Radio button 'is_correct' passes the value of the selected radio button which we set up as str(1..4)
            is_correct = (request.POST.get('is_correct') == str(i))
            
            if choice_text:  # Only save if choice was actually typed in
                Choice.objects.create(question=question, text=choice_text, is_correct=is_correct)
                
        messages.success(request, "Question added successfully!")
        return redirect('exam_detail', pk=exam.pk)

    return render(request, 'exams/add_question.html', {'exam': exam})

@login_required
def edit_question(request, pk):
    """
    Teacher edits a specific question and its choices.
    """
    question = get_object_or_404(Question, pk=pk, exam__teacher=request.user)
    choices = list(question.choices.all())
    
    # Ensure exactly 4 choices are passed to the template
    while len(choices) < 4:
        choices.append(Choice(question=question, text='', is_correct=False))

    if request.method == 'POST':
        question.text = request.POST.get('question_text')
        question.section_name = request.POST.get('section_name', 'General')
        question.marks = request.POST.get('marks', 1)
        question.explanation = request.POST.get('explanation', '')
        question.save()

        # Overwrite all choices to capture changes securely
        question.choices.all().delete()
        for i in range(1, 5):
            choice_text = request.POST.get(f'choice_{i}')
            is_correct = (request.POST.get('is_correct') == str(i))
            if choice_text:
                Choice.objects.create(question=question, text=choice_text, is_correct=is_correct)
                
        messages.success(request, "Question updated successfully!")
        return redirect('exam_detail', pk=question.exam.pk)

    return render(request, 'exams/edit_question.html', {'question': question, 'choices': choices})

@login_required
def bulk_add_questions(request, pk):
    """
    Advanced 'Fast Paste AI' parser endpoint.
    Retrieves raw text input containing multiple questions, choices, and answers
    formatted with specific syntax markers (e.g., [SECTION: X], [x], MARKS: Y).
    Parses strings securely into relational database nodes (Questions and Choices) 
    via regex and string manipulation to rapidly build large question banks.
    """
    exam = get_object_or_404(Exam, pk=pk, teacher=request.user)
    if request.method == 'POST':
        # --- NEW: FAST PASTE TEXT PARSER ---
        if 'raw_questions_text' in request.POST:
            raw_text = request.POST.get('raw_questions_text', '')
            if raw_text:
                try:
                    lines = raw_text.strip().split('\n')
                    current_section = "General"
                    current_question = None
                    current_marks = 1
                    choices = []
                    questions_created = 0
                    
                    import re
                    
                    for line in lines:
                        line = line.strip()
                        if not line: continue # Skip empty lines
                        
                        # Parse section headers (e.g., [SECTION: Aptitude])
                        if line.upper().startswith('[SECTION:') or line.upper().startswith('SECTION:'):
                            current_section = line.split(':', 1)[1].strip().strip(']')
                            continue
                            
                        # Parse MARKS lines (e.g., MARKS: 2)
                        if line.upper().startswith('MARKS:'):
                            try:
                                current_marks = int(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                            continue
                            
                        # Parse ANSWER lines (e.g., ANSWER: C)
                        if line.upper().startswith('ANSWER:'):
                            ans_letter = line.split(':', 1)[1].strip().upper()
                            correct_idx = ord(ans_letter) - 65 # Convert A->0, B->1, etc.
                            
                            # Save the question since we've reached the end of its block
                            if current_question and choices:
                                q_obj = Question.objects.create(
                                    exam=exam, text=current_question, 
                                    section_name=current_section, marks=current_marks
                                )
                                for i, c_text in enumerate(choices):
                                    Choice.objects.create(
                                        question=q_obj, text=c_text, is_correct=(i == correct_idx)
                                    )
                                questions_created += 1
                                current_question = None
                                choices = []
                                current_marks = 1  # Reset marks for next question
                            continue
                            
                        # Parse Choice lines (e.g., A. Choice Text or B) Choice Text)
                        match = re.match(r'^([A-D])[\.\)]\s*(.*)', line, re.IGNORECASE)
                        if match:
                            choices.append(match.group(2).strip())
                        else:
                            # Parse Question Text
                            if current_question is None:
                                current_question = line
                            else:
                                current_question += "\n" + line
                                
                    messages.success(request, f"{questions_created} questions added instantly via Fast Paste!")
                    return redirect('exam_detail', pk=exam.pk)
                except Exception as e:
                    messages.error(request, f"Error parsing text format: {str(e)}")
                    
        # --- EXISTING: JSON BUILDER PARSER ---
        else:
            try:
                questions_data = json.loads(request.POST.get('questions_json', '[]'))
                for q_data in questions_data:
                    question = Question.objects.create(
                        exam=exam,
                        text=q_data.get('text'),
                        section_name=q_data.get('section_name', 'General'),
                        marks=int(q_data.get('marks', 1))
                    )
                    choices = q_data.get('choices', [])
                    for idx, choice_text in enumerate(choices, start=1):
                        # Validate against whichever index the user selected as correct
                        is_correct = (str(idx) == str(q_data.get('correct_choice')))
                        if choice_text:
                            Choice.objects.create(question=question, text=choice_text, is_correct=is_correct)
                
                messages.success(request, f"{len(questions_data)} questions successfully imported!")
                return redirect('exam_detail', pk=exam.pk)
            except Exception as e:
                messages.error(request, f"Error processing bulk import: {str(e)}")
            
    return render(request, 'exams/bulk_add_questions.html', {'exam': exam})

@login_required
def delete_question(request, pk):
    """
    Teacher deletes a specific question from an exam.
    """
    question = get_object_or_404(Question, pk=pk, exam__teacher=request.user)
    if request.method == 'POST':
        exam_id = question.exam.id
        question.delete()
        messages.success(request, "Question deleted successfully.")
        return redirect('exam_detail', pk=exam_id)
    return redirect('home')

@login_required
def view_exam_results(request, pk):
    """
    Teacher views results for a specific exam they authored.
    """
    if not getattr(request.user, 'is_teacher', False):
        messages.error(request, "Access denied.")
        return redirect('home')
        
    exam = get_object_or_404(Exam, pk=pk, teacher=request.user)
    results = Result.objects.filter(exam=exam).order_by('-score', 'completed_at')
    
    # Calculate Analytics
    total_attempts = results.count()
    
    passed_count = 0
    failed_count = 0
    score_dist = [0, 0, 0, 0] # 0-25, 26-50, 51-75, 76-100
    
    for r in results:
        if r.is_pass:
            passed_count += 1
        else:
            failed_count += 1
            
        if r.attempt_total_marks > 0:
            perc = (r.score / r.attempt_total_marks) * 100
            if perc <= 25: score_dist[0] += 1
            elif perc <= 50: score_dist[1] += 1
            elif perc <= 75: score_dist[2] += 1
            else: score_dist[3] += 1
            
    avg_score = 0
    top_score = 0
    if total_attempts > 0:
        import django.db.models as models
        avg_score = round(results.aggregate(models.Avg('score'))['score__avg'], 1)
        top_score = results.aggregate(models.Max('score'))['score__max']

    context = {
        'exam': exam,
        'results': results,
        'kpi_total': total_attempts,
        'kpi_passed': passed_count,
        'kpi_failed': failed_count,
        'kpi_avg': avg_score,
        'kpi_top': top_score,
        'pass_percentage': round((passed_count / total_attempts * 100), 1) if total_attempts > 0 else 0,
        'score_dist': score_dist
    }
    
    return render(request, 'exams/view_results.html', context)

@login_required
def delete_exam(request, pk):
    """
    Teacher deletes an entire exam and all associated data.
    """
    exam = get_object_or_404(Exam, pk=pk, teacher=request.user)
    if request.method == 'POST':
        exam.delete()
        messages.success(request, "Examination deleted successfully.")
    return redirect('teacher_dashboard')

# --- STUDENT VIEWS ---

@login_required
def student_dashboard(request):
    """
    Renders the Student Interface mapped strictly out of the Examify ecosystem.
    Calculates and packages data including Available Exams (filtered dynamically
    by Department and Semester) and historical Academic Transcripts.
    Outputs comprehensive KPIs such as pass/fail ratios and colored score indications.
    """
    if not getattr(request.user, 'is_student', False):
        messages.error(request, "Access denied. Only students can view this page.")
        return redirect('home')
        
    # Re-attempt Logic: Get all exams the student has taken
    taken_results = Result.objects.filter(student=request.user)
    
    # Identify exams that are fully completed (either passed, or used up both attempts, or re-attempts not allowed after first fail)
    completed_exam_ids = []
    attempt_counts = {}
    
    for res in taken_results:
        exam_id = res.exam.id
        
        if res.is_pass:
            # If they passed once, they are done with this exam.
            completed_exam_ids.append(exam_id)
        else:
            # If they failed, track attempts.
            attempt_counts[exam_id] = res.attempt_number
            # If failed twice, or re-attempts are disabled
            if res.attempt_number >= 2 or not res.exam.allow_reattempt:
                completed_exam_ids.append(exam_id)

    available_exams = Exam.objects.exclude(id__in=completed_exam_ids)
    
    # Department Filtering: Ensure students only see exams intended for their department
    if getattr(request.user, 'department', None):
        from django.db.models import Q
        available_exams = available_exams.filter(
            Q(department=request.user.department) | Q(department__isnull=True)
        )
        
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

        
    selected_course_id = request.GET.get('course_id')
    if selected_course_id:
        available_exams = available_exams.filter(course_id=selected_course_id)
        
    from payments.models import Payment
    now = timezone.now()
    active_exams = []
    upcoming_exams = []
    
    for exam in available_exams:
        attempts = attempt_counts.get(exam.id, 0)
        exam.is_reattempt = attempts > 0
            
        if exam.scheduled_date:
            if exam.scheduled_date > now:
                upcoming_exams.append(exam)
            else:
                active_exams.append(exam)
        else:
            active_exams.append(exam)
            
    past_results = Result.objects.filter(student=request.user).order_by('-completed_at')
    
    # MCA Level KPI Calculations
    total_attempted = past_results.count()
    passed_count = 0
    total_percentage_sum = 0
    
    passed_exam_ids = {r.exam.id for r in past_results if r.is_pass}
    
    enriched_results = []
    for res in past_results:
        res.percentage = round((res.score / res.attempt_total_marks) * 100, 2) if res.attempt_total_marks > 0 else 0
        res.exam_passed_overall = res.exam.id in passed_exam_ids
        res.color = '#38a169' if res.is_pass or res.exam_passed_overall else '#e53e3e'
        enriched_results.append(res)
        total_percentage_sum += res.percentage
        if res.is_pass: passed_count += 1

    total_score_sum = sum(res.score for res in past_results)
    total_max_sum = sum(res.attempt_total_marks for res in past_results)
        
    avg_score = round(total_percentage_sum / total_attempted, 2) if total_attempted > 0 else 0
    avg_raw = round(total_score_sum / total_attempted, 1) if total_attempted > 0 else 0
    max_avg = round(total_max_sum / total_attempted, 1) if total_attempted > 0 else 0
    
    context = {
        'active_exams': active_exams,
        'upcoming_exams': upcoming_exams,
        'past_results': enriched_results,
        'kpi_total_attempted': total_attempted,
        'kpi_passed_count': passed_count,
        'kpi_avg_score': avg_score,
        'kpi_avg_raw': avg_raw,
        'kpi_max_avg': max_avg,
        'student_courses': student_courses,
        'selected_course_id': int(selected_course_id) if selected_course_id else None,
        'now': now,
    }
    return render(request, 'exams/student_dashboard.html', context)

@login_required
def take_exam(request, pk):
    """
    Handles live interaction of taking an exam by the student object.
    Implements a strict single-submission policy per student per exam.
    On POST (submission), calculates scores including dynamic negative marking logic
    (deducts fractional/decimal amounts per incorrect answer instead of 0).
    Saves and generates the corresponding Result metric object asynchronously.
    """
    if not getattr(request.user, 'is_student', False):
        return redirect('home')
        
    exam = get_object_or_404(Exam, pk=pk)
    
    # Check if student already took it and if re-attempt is allowed
    past_result = Result.objects.filter(student=request.user, exam=exam).first()
    total_attempts = past_result.attempt_number if past_result else 0
    
    # If they passed already, no more attempts
    if past_result and past_result.is_pass:
        messages.warning(request, "You have already passed this exam.")
        return redirect('student_dashboard')
        
    # If they've used up their attempts (max 2)
    if total_attempts >= 2:
        messages.warning(request, "Maximum attempts reached for this exam.")
        return redirect('student_dashboard')
        
    if total_attempts == 1:
        # Check if re-attempts are disabled
        if not exam.allow_reattempt:
            messages.warning(request, "Re-attempts are not permitted for this examination.")
            return redirect('student_dashboard')

    if request.method == 'POST':
        score = 0
        
        rendered_question_ids = request.POST.get('rendered_question_ids', '')
        if rendered_question_ids:
            rendered_ids = [int(i) for i in rendered_question_ids.split(',')]
            exam_questions = exam.questions.filter(id__in=rendered_ids)
        else:
            exam_questions = exam.questions.all()
        
        violations = int(request.POST.get('violations', 0))
        
        result = Result.objects.filter(student=request.user, exam=exam).first()
        if result:
            result.attempt_number += 1
            result.proctoring_violations = violations
            result.score = 0
            from django.utils import timezone
            result.completed_at = timezone.now()
            result.save()
            result.answers.all().delete()
        else:
            result = Result.objects.create(
                student=request.user, 
                exam=exam, 
                score=0, 
                proctoring_violations=violations,
                attempt_number=1
            )
        
        from results.models import StudentAnswer
        
        # For each question, find what the student submitted
        for q in exam_questions:
            selected_choice_id = request.POST.get(f'question_{q.id}')
            choice = None
            if selected_choice_id:
                try:
                    choice = Choice.objects.get(id=selected_choice_id)
                    if choice.is_correct:
                        score += q.marks
                    elif exam.negative_marks > 0:
                        score -= exam.negative_marks
                except Choice.DoesNotExist:
                    pass
            
            # Save the answer regardless of whether it was correct or even selected
            StudentAnswer.objects.create(
                result=result,
                question=q,
                selected_choice=choice
            )
        
        # Prevent negative score
        score = max(0, score)
                    
        # Update Result with final score
        result.score = score
        result.save()
        
        messages.success(request, f"Exam submitted! Your score is {score}/{result.attempt_total_marks}")
        return redirect('view_answer_sheet', pk=result.pk)
        
    # GET request - prepare questions
    questions_list = list(exam.questions.all())
    
    # Random selection logic if enabled
    if exam.random_question_count > 0 and len(questions_list) > exam.random_question_count:
        questions = random.sample(questions_list, exam.random_question_count)
    else:
        questions = questions_list
        if exam.shuffle_questions:
            random.shuffle(questions)
        
    return render(request, 'exams/take_exam.html', {'exam': exam, 'questions': questions, 'hide_nav': True})

@login_required
def view_answer_sheet(request, pk):
    """
    Shows the student their submitted answers, correct answers, and score breakdown.
    'pk' is the Result ID.
    """
    result = get_object_or_404(Result, pk=pk, student=request.user)
    # Prefetch answers and questions for performance
    answers = result.answers.all().select_related('question', 'selected_choice')
    
    # Enrich answers with correctness and correct choice
    enriched_answers = []
    for ans in answers:
        correct_choice = Choice.objects.filter(question=ans.question, is_correct=True).first()
        ans.correct_choice = correct_choice
        ans.is_correct = (ans.selected_choice == correct_choice)
        enriched_answers.append(ans)
        
    result.percentage = round((result.score / result.attempt_total_marks) * 100, 2) if result.attempt_total_marks > 0 else 0
    result.passing_marks = result.attempt_total_marks / 2


    return render(request, 'exams/view_answer_sheet.html', {
        'result': result,
        'enriched_answers': enriched_answers,
        'kpi_total': result.total_questions_count,
        'kpi_unattempted': result.unattempted_count
    })

@login_required
def student_analytics(request):
    """
    Dedicated page for student performance analytics with enhanced robustness.
    """
    if not getattr(request.user, 'is_student', False):
        return redirect('home')
        
    # Order by completed_at to show a proper timeline in the chart
    past_results = Result.objects.filter(student=request.user).order_by('completed_at')
    
    # Prep data for charts with formatted labels
    labels = []
    scores = []
    total_marks = []
    percentages = []
    # Determine overall pass status per exam
    passed_exam_ids = set()
    for res in past_results:
        if res.is_pass:
            passed_exam_ids.add(res.exam.id)

    enriched_results = []
    for res in past_results:
        pct = round((res.score / res.attempt_total_marks) * 100, 2) if res.attempt_total_marks > 0 else 0
        res.percentage = pct
        res.exam_passed_overall = res.exam.id in passed_exam_ids
        enriched_results.append(res)
        
        # Formatted label: "Title (Date)"
        labels.append(f"{res.exam.title} ({res.completed_at.strftime('%b %d')})")
        scores.append(res.score)
        total_marks.append(res.attempt_total_marks)
        percentages.append(pct)
    
    # Calculate KPI Average Score
    kpi_avg_score = 0
    if percentages:
        kpi_avg_score = round(sum(percentages) / len(percentages), 2)

    context = {
        'labels': json.dumps(labels),
        'scores': json.dumps(scores),
        'total_marks': json.dumps(total_marks),
        'percentages': json.dumps(percentages),
        'past_results': enriched_results,
        'kpi_avg_score': kpi_avg_score,
    }
    return render(request, 'exams/student_analytics.html', context)


@login_required
def download_result_pdf(request, pk):
    """
    Generates a professional PDF transcript of a specific result.
    Uses xhtml2pdf to convert a specialized HTML template into a 
    portable document format (PDF) for offline student records.
    """
    result = get_object_or_404(Result, pk=pk, student=request.user)
    
    # Enrich answers for the PDF
    answers = result.answers.all().select_related('question', 'selected_choice')
    enriched_answers = []
    letters = ['A', 'B', 'C', 'D']
    
    for ans in answers:
        # Get all choices for this question
        all_choices = list(ans.question.choices.all())
        correct_choice = None
        
        # Format choices for the PDF grid
        formatted_choices = []
        for i, choice in enumerate(all_choices):
            letter = letters[i] if i < len(letters) else '?'
            is_selected = (ans.selected_choice == choice)
            
            if choice.is_correct:
                correct_choice = choice
            
            formatted_choices.append({
                'letter': letter,
                'text': choice.text,
                'is_correct': choice.is_correct,
                'is_selected': is_selected,
                'status_class': 'correct' if choice.is_correct else ('wrong' if is_selected else '')
            })
        
        ans.formatted_choices = formatted_choices
        ans.correct_choice = correct_choice
        ans.is_correct = (ans.selected_choice == correct_choice)
        enriched_answers.append(ans)
        
    result.percentage = round((result.score / result.exam.total_marks) * 100, 1) if result.exam.total_marks > 0 else 0
    
    context = {
        'result': result,
        'enriched_answers': enriched_answers,
        'kpi_total': result.total_questions_count,
        'kpi_correct': result.correct_answers_count,
        'kpi_wrong': result.wrong_answers_count,
        'kpi_unattempted': result.unattempted_count,
        'now': timezone.now(),
    }
    
    # Load template and render it with context
    template = get_template('exams/result_pdf.html')
    html = template.render(context)
    
    # Create a bytes buffer for the PDF
    result_buffer = io.BytesIO()
    
    # Generate PDF
    pisa_status = pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=result_buffer)
    
    # If error occurred, return error response
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    
    # Prepare response
    filename = f"Result_{result.exam.title.replace(' ', '_')}_{result.student.username}.pdf"
    response = HttpResponse(result_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

