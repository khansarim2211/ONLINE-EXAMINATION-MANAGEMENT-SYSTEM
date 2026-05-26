{% extends 'base.html' %}

{% block content %}

<!-- KPI Metrics Grid -->
<div id="analytics-section" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-bottom: 3rem;">
    <div class="glass-panel"
        style="display: flex; align-items: center; gap: 1.5rem; padding: 1.5rem; border-left: 4px solid var(--primary-color); transition: transform 0.2s;"
        onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='none'">
        <div style="background: var(--primary-light); color: var(--primary-color); padding: 1rem; border-radius: 12px; font-size: 2rem;">
            <i class="fa-solid fa-clipboard-list"></i>
        </div>
        <div>
            <h4 style="color: var(--text-muted); margin: 0; font-size: 0.9rem; text-transform: uppercase;">Total Exams Taken</h4>
            <div style="font-size: 2.2rem; font-weight: 800; color: var(--text-main);">{{ kpi_total_attempted }}</div>
        </div>
    </div>

    <div class="glass-panel"
        style="display: flex; align-items: center; gap: 1.5rem; padding: 1.5rem; border-left: 4px solid #38a169; transition: transform 0.2s;"
        onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='none'">
        <div style="background: #f0fff4; color: #38a169; padding: 1rem; border-radius: 12px; font-size: 2rem;">
            <i class="fa-solid fa-check-circle"></i>
        </div>
        <div>
            <h4 style="color: var(--text-muted); margin: 0; font-size: 0.9rem; text-transform: uppercase;">Exams Passed</h4>
            <div style="font-size: 2.2rem; font-weight: 800; color: var(--text-main);">{{ kpi_passed_count }}</div>
        </div>
    </div>

    <div class="glass-panel"
        style="display: flex; align-items: center; gap: 1.5rem; padding: 1.5rem; border-left: 4px solid #3182ce; transition: transform 0.2s;"
        onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='none'">
        <div style="background: #ebf8ff; color: #3182ce; padding: 1rem; border-radius: 12px; font-size: 2rem;">
            <i class="fa-solid fa-chart-line"></i>
        </div>
        <div>
            <h4 style="color: var(--text-muted); margin: 0; font-size: 0.9rem; text-transform: uppercase;">Average Score</h4>
            <div style="font-size: 2.2rem; font-weight: 800; color: var(--text-main);">{{ kpi_avg_score }}%</div>
        </div>
    </div>
</div>

<div style="margin-top: 2rem;">
    <h3 style="border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem;">My Subjects (Semester {{ user.semester|default:"N/A" }})</h3>
    {% if student_courses %}
        <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem; margin-bottom: 2rem;">
            <a href="{% url 'student_dashboard' %}" 
               style="text-decoration: none; padding: 0.8rem 1.5rem; border-radius: 8px; font-weight: bold; transition: all 0.2s ease;
               {% if not selected_course_id %}background-color: var(--primary-color); color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);{% else %}background-color: white; color: #4a5568; border: 1px solid #e2e8f0;{% endif %}">
                All Subjects
            </a>
            {% for course in student_courses %}
                <a href="{% url 'student_dashboard' %}?course_id={{ course.id }}" 
                   style="text-decoration: none; padding: 0.8rem 1.5rem; border-radius: 8px; font-weight: bold; transition: all 0.2s ease;
                   {% if selected_course_id == course.id %}background-color: var(--primary-color); color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);{% else %}background-color: white; color: #4a5568; border: 1px solid #e2e8f0;{% endif %}">
                    {{ course.name }}
                </a>
            {% endfor %}
        </div>
    {% else %}
        <p style="color: #718096;">No subjects found for your current semester.</p>
    {% endif %}
</div>

<div class="glass-panel" style="padding: 0; overflow: hidden; margin-bottom: 3rem;">
    <h3 style="padding: 1.5rem; margin: 0; border-bottom: 1px solid rgba(255,255,255,0.4); background: rgba(255,255,255,0.5);">
        Active Exams
    </h3>
    {% if active_exams %}
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                <tr style="background-color: rgba(248, 250, 252, 0.8); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted);">
                    <th style="padding: 1rem 1.5rem;">Title / Course</th>
                    <th style="padding: 1rem 1.5rem;">Duration</th>
                    <th style="padding: 1rem 1.5rem;">Marks</th>
                    <th style="padding: 1rem 1.5rem;">Action</th>
                </tr>
                {% for exam in active_exams %}
                <tr style="border-bottom: 1px solid rgba(226, 232, 240, 0.5); transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='rgba(255,255,255,0.9)'" onmouseout="this.style.backgroundColor='transparent'">
                    <td style="padding: 1.25rem 1.5rem;">
                        <strong style="font-size: 1.1rem; color: var(--text-main); display: block;">{{ exam.title }}</strong>
                        <span style="color: var(--text-muted); font-size: 0.9rem;">{{ exam.course.name }}</span>
                    </td>
                    <td style="padding: 1.25rem 1.5rem; color: var(--text-muted); font-weight: 600;">
                        {{ exam.duration_minutes }} Min
                    </td>
                    <td style="padding: 1.25rem 1.5rem; color: var(--text-main); font-weight: 600;">
                        {{ exam.total_marks }}
                    </td>
                    <td style="padding: 1.25rem 1.5rem;">
                        {% if exam.is_reattempt %}
                            <span style="display: block; font-size: 0.65rem; font-weight: 900; color: #ef4444; text-transform: uppercase; margin-bottom: 0.3rem;">Re-attempt</span>
                        {% endif %}
                        {% if exam.needs_payment and not exam.has_paid %}
                            <a href="{% url 'initiate_payment' exam.id %}" class="btn btn-primary" style="padding: 0.5rem 1rem; border-radius: 50px; font-size: 0.9rem; font-weight: bold; background-color: #4f46e5; border-color: #4f46e5; box-shadow: 0 4px 10px rgba(79,70,229,0.2);">
                                Pay ₹{{ exam.reattempt_price }}
                            </a>
                        {% else %}
                            <a href="{% url 'take_exam' exam.pk %}" class="btn btn-primary" style="padding: 0.5rem 1rem; border-radius: 50px; font-size: 0.9rem; font-weight: bold; box-shadow: 0 4px 10px rgba(37,99,235,0.2);">
                                Take Exam
                            </a>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    {% else %}
        <div style="padding: 2rem; text-align: center;">
            <p style="color: var(--text-muted);">No active exams at the moment.</p>
        </div>
    {% endif %}
</div>

<div class="glass-panel" style="padding: 0; overflow: hidden; margin-bottom: 3rem;">
    <h3 style="padding: 1.5rem; margin: 0; border-bottom: 1px solid rgba(255,255,255,0.4); background: rgba(255,255,255,0.5);">
        Upcoming Exams
    </h3>
    {% if upcoming_exams %}
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                <tr style="background-color: rgba(248, 250, 252, 0.8); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted);">
                    <th style="padding: 1rem 1.5rem;">Title / Course</th>
                    <th style="padding: 1rem 1.5rem;">Scheduled For</th>
                    <th style="padding: 1rem 1.5rem;">Duration</th>
                    <th style="padding: 1rem 1.5rem;">Status</th>
                </tr>
                {% for exam in upcoming_exams %}
                <tr style="border-bottom: 1px solid rgba(226, 232, 240, 0.5); transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='rgba(255,255,255,0.9)'" onmouseout="this.style.backgroundColor='transparent'">
                    <td style="padding: 1.25rem 1.5rem;">
                        <strong style="font-size: 1.1rem; color: var(--text-main); display: block;">{{ exam.title }}</strong>
                        <span style="color: var(--text-muted); font-size: 0.9rem;">{{ exam.course.name }}</span>
                    </td>
                    <td style="padding: 1.25rem 1.5rem; color: var(--primary-color); font-weight: 700;">
                        {{ exam.scheduled_date|date:"M d, Y H:i" }}
                    </td>
                    <td style="padding: 1.25rem 1.5rem; color: var(--text-muted); font-weight: 600;">
                        {{ exam.duration_minutes }} Min
                    </td>
                    <td style="padding: 1.25rem 1.5rem;">
                        <span style="background-color: #fef9c3; color: #854d0e; padding: 0.4rem 1rem; border-radius: 50px; font-size: 0.85rem; border: 1px solid #fef08a; font-weight: 700;">
                            Locked
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    {% else %}
        <div style="padding: 2rem; text-align: center;">
            <p style="color: var(--text-muted);">No upcoming exams scheduled.</p>
        </div>
    {% endif %}
</div>

<div class="glass-panel" style="padding: 0; overflow: hidden; margin-bottom: 3rem;">
    <h3 style="padding: 1.5rem; margin: 0; border-bottom: 1px solid rgba(255,255,255,0.4); background: rgba(255,255,255,0.5);">
        Academic Transcript (Results)
    </h3>
    {% if past_results %}
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                <tr style="background-color: rgba(248, 250, 252, 0.8); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted);">
                    <th style="padding: 1rem 1.5rem;">Date Taken</th>
                    <th style="padding: 1rem 1.5rem;">Exam Details</th>
                    <th style="padding: 1rem 1.5rem;">Score</th>
                    <th style="padding: 1rem 1.5rem;">Status</th>
                </tr>
                {% for res in past_results %}
                <tr style="border-bottom: 1px solid rgba(226, 232, 240, 0.5); transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='rgba(255,255,255,0.9)'" onmouseout="this.style.backgroundColor='transparent'">
                    <td style="padding: 1.25rem 1.5rem; color: var(--text-muted); font-size: 0.95rem;">
                        {{ res.completed_at|date:"M d, Y H:i" }}
                    </td>
                    <td style="padding: 1.25rem 1.5rem;">
                        <strong style="font-size: 1.1rem; color: var(--text-main); display: block;">{{ res.exam.title }}</strong>
                        <span style="color: var(--text-muted); font-size: 0.9rem;">{{ res.exam.course.name }}</span>
                    </td>
                    <td style="padding: 1.25rem 1.5rem; font-weight: 800; font-size: 1.15rem; color: {{ res.color }};">
                        {{ res.score }} <span style="font-size: 0.85rem; color: var(--text-muted); font-weight: 500;">/ {{ res.exam.total_marks }}</span>
                    </td>
                    <td style="padding: 1.25rem 1.5rem; font-weight: 800;">
                        {% if res.is_pass %}
                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                <a href="{% url 'view_answer_sheet' res.pk %}" style="text-decoration: none; background-color: #f0fff4; color: #16a34a; padding: 0.4rem 1rem; border-radius: 50px; font-size: 0.85rem; border: 1px solid #bbf7d0; display: inline-block;">
                                    Passed - View Details
                                </a>
                                <a href="{% url 'download_result_pdf' res.pk %}" title="Download PDF" style="color: #16a34a; font-size: 1.1rem; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.2)'" onmouseout="this.style.transform='scale(1)'">
                                    <i class="fa-solid fa-file-pdf"></i>
                                </a>
                            </div>
                        {% else %}
                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                <a href="{% url 'view_answer_sheet' res.pk %}" style="text-decoration: none; background-color: #fef2f2; color: #dc2626; padding: 0.4rem 1rem; border-radius: 50px; font-size: 0.85rem; border: 1px solid #fecaca; display: inline-block;">
                                    Failed - View Details
                                </a>
                                <a href="{% url 'download_result_pdf' res.pk %}" title="Download PDF" style="color: #dc2626; font-size: 1.1rem; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.2)'" onmouseout="this.style.transform='scale(1)'">
                                    <i class="fa-solid fa-file-pdf"></i>
                                </a>
                            </div>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    {% else %}
        <div style="padding: 3rem; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;">🎓</div>
            <p style="font-size: 1.1rem; color: var(--text-muted); margin-bottom: 1rem;">No prior academic records generated.</p>
        </div>
    {% endif %}
</div>
{% endblock %}
