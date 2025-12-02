from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.urls import reverse
from django.db.models import Q, Avg, Count, F
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
import secrets

from .models import (
    UserProfile, Course, Enrollment, Attendance,
    Marks, GradingScheme, StudentResult, AttendanceNotification, StudentRegistration
)
from .forms import (
    LoginForm, UserForm, UserProfileForm, PasswordChangeForm, CourseForm, EnrollmentForm,
    AttendanceForm, AttendanceBulkForm, MarksForm, GradingSchemeForm, StudentResultForm, StudentRegistrationForm
)


# ==================== Decorators ====================

def role_required(allowed_roles):
    """Decorator to check user role"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in first.")
                return redirect('login')

            try:
                user_role = request.user.profile.role
                if user_role not in allowed_roles:
                    messages.error(
                        request, "You don't have permission to access this page.")
                    return redirect('dashboard')
            except UserProfile.DoesNotExist:
                messages.error(
                    request, "User profile not found. Please contact administrator.")
                return redirect('login')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ==================== Authentication Views ====================

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Ensure user has a profile (create if missing)
                try:
                    profile = user.profile
                except UserProfile.DoesNotExist:
                    # Create profile for users created via createsuperuser
                    inferred_role = 'admin' if (
                        user.is_staff or user.is_superuser) else 'student'
                    profile = UserProfile.objects.create(
                        user=user,
                        role=inferred_role,
                        is_active=True
                    )

                if profile.is_active:
                    login(request, user)
                    messages.success(
                        request, f"Welcome back, {user.get_full_name()}!")
                    return redirect('dashboard')
                else:
                    messages.error(
                        request, "Your account has been deactivated. Contact admin.")
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    context = {'form': form}
    return render(request, 'app1/login.html', context)


@login_required(login_url='login')
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


# ==================== Dashboard Views ====================

@login_required(login_url='login')
def dashboard(request):
    """Main dashboard - routes to role-specific dashboard"""
    try:
        role = request.user.profile.role

        if role == 'admin':
            return admin_dashboard(request)
        elif role == 'teacher':
            return teacher_dashboard(request)
        elif role == 'student':
            return student_dashboard(request)
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('login')

    return redirect('login')


@role_required(['admin'])
def admin_dashboard(request):
    """Admin dashboard with system overview"""
    context = {
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(profile__role='student', profile__is_active=True).count(),
        'total_teachers': User.objects.filter(profile__role='teacher', profile__is_active=True).count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
        'total_enrollments': Enrollment.objects.filter(is_active=True).count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
    }
    return render(request, 'app1/dashboard/admin_dashboard.html', context)


@role_required(['teacher'])
def teacher_dashboard(request):
    """Teacher dashboard with their courses"""
    teacher = request.user
    courses = Course.objects.filter(instructor=teacher, is_active=True)

    context = {
        'courses': courses,
        'total_students': Enrollment.objects.filter(course__instructor=teacher, is_active=True).values('student').distinct().count(),
        'total_enrollments': Enrollment.objects.filter(course__instructor=teacher, is_active=True).count(),
    }
    return render(request, 'app1/dashboard/teacher_dashboard.html', context)


@role_required(['student'])
def student_dashboard(request):
    """Student dashboard with enrolled courses and grades"""
    student = request.user
    enrollments = Enrollment.objects.filter(
        student=student, is_active=True).select_related('course')

    # Calculate average attendance
    total_attendance = 0
    courses_with_attendance = 0

    for enrollment in enrollments:
        attendance_pct = enrollment.get_attendance_percentage()
        if enrollment.attendance_records.exists():
            total_attendance += attendance_pct
            courses_with_attendance += 1

    avg_attendance = round(total_attendance / courses_with_attendance,
                           2) if courses_with_attendance > 0 else 0

    context = {
        'enrollments': enrollments,
        'total_courses': enrollments.count(),
        'avg_attendance': avg_attendance,
    }
    return render(request, 'app1/dashboard/student_dashboard.html', context)


# ==================== User Management Views ====================

@role_required(['admin'])
def manage_users(request):
    """List and manage users"""
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('search', '')

    # Ensure every User has a UserProfile to avoid RelatedObjectDoesNotExist errors
    users_qs = User.objects.all()
    for u in users_qs:
        try:
            _ = u.profile
        except UserProfile.DoesNotExist:
            # Infer role from staff/superuser flags where appropriate
            inferred_role = 'admin' if (
                u.is_staff or u.is_superuser) else 'student'
            UserProfile.objects.create(
                user=u, role=inferred_role, is_active=False)

    users = User.objects.select_related('profile').all()

    if role_filter:
        users = users.filter(profile__role=role_filter)

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    context = {
        'users': users,
        'role_filter': role_filter,
        'search_query': search_query,
    }
    return render(request, 'app1/admin/manage_users.html', context)


@role_required(['admin'])
def delete_user(request, user_id):
    """Delete a user and their profile (admin only)"""
    user = get_object_or_404(User, id=user_id)
    # Prevent admin from deleting themselves accidentally
    if request.user.id == user.id:
        messages.error(
            request, "You cannot delete your own account while logged in.")
        return redirect('manage_users')

    try:
        user.delete()
        messages.success(
            request, f'User {user.username} and associated data have been deleted.')
    except Exception as e:
        messages.error(request, f'Error deleting user: {e}')

    return redirect('manage_users')


@role_required(['admin'])
def delete_student_registration(request, registration_id):
    """Delete a pending or verified student registration (admin only)"""
    registration = get_object_or_404(StudentRegistration, id=registration_id)
    try:
        registration.delete()
        messages.success(
            request, f'Student registration for {registration.email} has been deleted.')
    except Exception as e:
        messages.error(request, f'Error deleting registration: {e}')

    return redirect('manage_student_registrations')


# @role_required(['admin'])
# def add_user(request):
#     """Add new user"""
#     if request.method == 'POST':
#         user_form = UserForm(request.POST)
#         profile_form = UserProfileForm(request.POST)

#         if user_form.is_valid() and profile_form.is_valid():
#             # Create user
#             user = user_form.save(commit=False)
#             if user_form.cleaned_data['password']:
#                 user.set_password(user_form.cleaned_data['password'])
#             user.save()

#             # Create profile
#             profile = profile_form.save(commit=False)
#             profile.user = user
#             profile.role = request.POST.get('role', 'student')
#             profile.is_active = True
#             profile.save()

#             messages.success(
#                 request, f"User {user.username} created successfully!")
#             return redirect('manage_users')
#     else:
#         # Allow pre-filling the add-user form from query params (e.g., from registration)
#         initial_user = {}
#         initial_profile = {}

#         if request.GET.get('email'):
#             initial_user['email'] = request.GET.get('email')
#         if request.GET.get('username'):
#             initial_user['username'] = request.GET.get('username')
#         if request.GET.get('first_name'):
#             initial_user['first_name'] = request.GET.get('first_name')
#         if request.GET.get('last_name'):
#             initial_user['last_name'] = request.GET.get('last_name')
#         if request.GET.get('phone'):
#             initial_profile['phone'] = request.GET.get('phone')
#         if request.GET.get('parent_email'):
#             initial_profile['parent_email'] = request.GET.get('parent_email')

#         user_form = UserForm(initial=initial_user)
#         profile_form = UserProfileForm(initial=initial_profile)
#         # If role is provided, pass it to the template so it can be preselected
#         prefill_role = request.GET.get('role')

#     context = {
#         'user_form': user_form,
#         'profile_form': profile_form,
#         'page_title': 'Add New User',
#         'prefill_role': prefill_role if 'prefill_role' in locals() else None,
#     }
#     return render(request, 'app1/admin/add_edit_user.html', context)

@role_required(['admin'])
def add_user(request):
    """Add new user"""
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            # Get the plain-text password before saving/hashing
            plain_password = user_form.cleaned_data.get('password')

            # Create user
            user = user_form.save(commit=False)
            if plain_password:
                user.set_password(plain_password)
            user.save()

            # Create profile
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.role = request.POST.get('role', 'student')
            profile.is_active = True
            profile.save()

            messages.success(
                request, f"User {user.username} created successfully!")

            # --- START OF FIXED EMAIL SENDING BLOCK ---
            try:
                # Use the plain_password variable for the email body
                send_mail(
                    subject='Welcome! Your Student Account is Ready',
                    message=f"""
Hello {user.first_name} {user.last_name},

Congratulations! Your student account has been approved and is now ready to use.

YOUR LOGIN CREDENTIALS:

Username: {user.username}
Password: {plain_password}
Role: {profile.role}
Email: {user.email}


LOG IN HERE: http://AcademicSuite.pythonanywhere.com/login/

IMPORTANT:
1. Save your username and password in a safe place
2. After logging in, go to your profile and change your password
3. Keep your login credentials confidential

If you have any questions or issues logging in, please contact the administration.

Best regards,

Student Academic Suite Team
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    # FIX 1: Use user.email as the recipient.
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                pass
                # FIX 2: The print statement was incorrectly indented and missing context.
                # print(f"Error sending credentials email: {e}")
                # --- END OF FIXED EMAIL SENDING BLOCK ---

            return redirect('manage_users')
    else:
        # Allow pre-filling the add-user form from query params (e.g., from registration)
        initial_user = {}
        initial_profile = {}

        if request.GET.get('email'):
            initial_user['email'] = request.GET.get('email')
        if request.GET.get('username'):
            initial_user['username'] = request.GET.get('username')
        if request.GET.get('first_name'):
            initial_user['first_name'] = request.GET.get('first_name')
        if request.GET.get('last_name'):
            initial_user['last_name'] = request.GET.get('last_name')
        if request.GET.get('phone'):
            initial_profile['phone'] = request.GET.get('phone')
        if request.GET.get('parent_email'):
            initial_profile['parent_email'] = request.GET.get('parent_email')

        user_form = UserForm(initial=initial_user)
        profile_form = UserProfileForm(initial=initial_profile)
        # If role is provided, pass it to the template so it can be preselected
        prefill_role = request.GET.get('role')

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'page_title': 'Add New User',
        'prefill_role': prefill_role if 'prefill_role' in locals() else None,
    }
    return render(request, 'app1/admin/add_edit_user.html', context)


@role_required(['admin'])
def edit_user(request, user_id):
    """Edit user details"""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            if user_form.cleaned_data['password']:
                user.set_password(user_form.cleaned_data['password'])
            user.save()
            profile_form.save()

            messages.success(
                request, f"User {user.username} updated successfully!")
            return redirect('manage_users')
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'page_title': f'Edit User: {user.get_full_name()}',
        'user_obj': user,
    }
    return render(request, 'app1/admin/add_edit_user.html', context)


@role_required(['admin'])
def deactivate_user(request, user_id):
    """Deactivate user account"""
    user = get_object_or_404(User, id=user_id)
    user.profile.is_active = False
    user.profile.save()
    messages.success(request, f"User {user.username} has been deactivated.")
    return redirect('manage_users')


@role_required(['admin'])
def activate_user(request, user_id):
    """Activate user account"""
    user = get_object_or_404(User, id=user_id)
    user.profile.is_active = True
    user.profile.save()
    messages.success(request, f"User {user.username} has been activated.")
    return redirect('manage_users')


# ==================== Course Management Views ====================

@role_required(['admin'])
def manage_courses(request):
    """List and manage courses"""
    courses = Course.objects.select_related('instructor').all()

    context = {'courses': courses}
    return render(request, 'app1/admin/manage_courses.html', context)


@role_required(['admin'])
def add_course(request):
    """Add new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()

            # Create default grading scheme
            GradingScheme.objects.get_or_create(
                course=course,
                defaults={
                    'assignment_percentage': 10,
                    'quiz_percentage': 10,
                    'midterm_percentage': 30,
                    'final_percentage': 50,
                }
            )

            messages.success(
                request, f"Course {course.code} created successfully!")
            return redirect('manage_courses')
    else:
        form = CourseForm()

    context = {
        'form': form,
        'page_title': 'Add New Course',
    }
    return render(request, 'app1/admin/add_edit_course.html', context)


@role_required(['admin'])
def edit_course(request, course_id):
    """Edit course details"""
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Course {course.code} updated successfully!")
            return redirect('manage_courses')
    else:
        form = CourseForm(instance=course)

    context = {
        'form': form,
        'page_title': f'Edit Course: {course.code}',
        'course': course,
    }
    return render(request, 'app1/admin/add_edit_course.html', context)


@role_required(['admin'])
def delete_course(request, course_id):
    """Delete a course"""
    course = get_object_or_404(Course, id=course_id)
    course_code = course.code
    course_name = course.name

    try:
        course.delete()
        messages.success(
            request, f'Course {course_code} - {course_name} has been deleted.')
    except Exception as e:
        messages.error(request, f'Error deleting course: {e}')

    return redirect('manage_courses')


# ==================== Enrollment Management Views ====================

@role_required(['admin'])
def manage_enrollments(request):
    """List and manage enrollments"""
    enrollments = Enrollment.objects.select_related('student', 'course').all()

    context = {'enrollments': enrollments}
    return render(request, 'app1/admin/manage_enrollments.html', context)


@role_required(['admin'])
def delete_enrollment(request, enrollment_id):
    """Delete/unenroll a student from a course"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    student_name = enrollment.student.get_full_name()
    course_code = enrollment.course.code

    try:
        enrollment.delete()
        messages.success(
            request, f'{student_name} has been unenrolled from {course_code}.')
    except Exception as e:
        messages.error(request, f'Error unenrolling student: {e}')

    return redirect('manage_enrollments')


@role_required(['admin'])
def add_enrollment(request):
    """Add student to course"""
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enrollment = form.save()

            # Create result record if needed
            StudentResult.objects.get_or_create(enrollment=enrollment)

            messages.success(request, f"Student enrolled successfully!")
            return redirect('manage_enrollments')
    else:
        form = EnrollmentForm()

    context = {
        'form': form,
        'page_title': 'Add Enrollment',
    }
    return render(request, 'app1/admin/add_edit_enrollment.html', context)


# ==================== Attendance Views ====================

@role_required(['teacher'])
def mark_attendance(request):
    """Mark attendance for a course"""
    from datetime import datetime, date as _date

    teacher = request.user
    enrollments = None
    selected_course = None
    selected_date = None
    form = AttendanceBulkForm(teacher=teacher)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        selected_date_str = request.POST.get('date', '').strip()

        # Always try to load course and date from POST (whether Load Students button or Submit button)
        if request.POST.get('course'):
            course_id = request.POST.get('course')
            try:
                selected_course = Course.objects.get(
                    id=course_id, instructor=teacher)
                # Parse the date string if provided
                date_obj = None
                if selected_date_str:
                    try:
                        date_obj = datetime.strptime(
                            selected_date_str, '%Y-%m-%d').date()
                        # keep selected_date as a date object so the template date filter works reliably
                        selected_date = date_obj
                    except ValueError:
                        messages.error(request, 'Invalid date format.')
                        date_obj = None

                # Always build enrollment data (for both Load Students and Submit)
                base_enrollments = Enrollment.objects.filter(
                    course=selected_course, is_active=True).order_by('student__first_name', 'student__last_name')
                enrollments = []
                for enrollment in base_enrollments:
                    enrollment_data = {
                        'enrollment': enrollment,
                        'student_name': enrollment.student.get_full_name(),
                        'student_email': enrollment.student.email,
                        'current_attendance': None,
                        'previous_attendance': None,
                    }
                    # Load previous attendance for selected date if provided
                    if date_obj:
                        try:
                            prev_attendance = Attendance.objects.get(
                                enrollment=enrollment, date=date_obj)
                            enrollment_data['current_attendance'] = prev_attendance.status
                            enrollment_data['previous_attendance'] = prev_attendance.status
                        except Attendance.DoesNotExist:
                            enrollment_data['current_attendance'] = None
                            enrollment_data['previous_attendance'] = None
                    enrollments.append(enrollment_data)
            except Course.DoesNotExist:
                messages.error(
                    request, 'Selected course not found or you are not the instructor.')
                selected_course = None
                enrollments = None

        # Load students for selected course (teacher clicked "Load Students")
        # NOTE: enrollments are now always loaded upfront, so this just ensures display
        if action == 'load_students' and request.POST.get('course'):
            pass  # enrollments already loaded above

        # Submit attendance: require both course and date
        elif request.POST.get('course') and request.POST.get('date'):
            form = AttendanceBulkForm(teacher=teacher, data=request.POST)

            submitted_date = request.POST.get('date')
            submitted_course = request.POST.get('course')
            submitted_statuses = [
                k for k in request.POST.keys() if k.startswith('status_')]

            # enrollments already loaded upfront, just need to save
            if selected_course and selected_date and form.is_valid():
                # Parse the date for saving. Accept either a date object or a string.
                date = None
                try:
                    # If selected_date is already a date object, use it directly
                    from datetime import date as _date
                    if isinstance(selected_date, _date):
                        date = selected_date
                    else:
                        date = datetime.strptime(
                            str(selected_date), '%Y-%m-%d').date()
                except Exception:
                    date = None

                if date:
                    # Save attendance for all submitted statuses
                    attendance_count = 0
                    for enrollment in (enrollments or []):
                        status = request.POST.get(
                            f'status_{enrollment["enrollment"].id}', '')
                        if status:
                            try:
                                attendance, created = Attendance.objects.update_or_create(
                                    enrollment=enrollment['enrollment'],
                                    date=date,
                                    defaults={
                                        'status': status,
                                        'marked_by': teacher
                                    }
                                )
                                # saved successfully
                            except Exception as e:
                                messages.error(
                                    request, f"Error saving attendance for {enrollment['student_name']}: {e}")
                                continue
                            attendance_count += 1

                    if attendance_count > 0:
                        check_and_send_attendance_notifications(
                            selected_course)
                        messages.success(
                            request, f"Attendance marked for {attendance_count} students successfully!")
                    else:
                        messages.warning(
                            request, "No attendance status was selected for any student.")

                    # Redirect back to the mark attendance page without query params
                    # to avoid persisting a previous date that may confuse the user.
                    return redirect('mark_attendance')
            else:
                messages.error(
                    request, "Could not process attendance submission. Please try again.")
                return redirect('mark_attendance')

    # If teacher was redirected here with query params, load enrollments for GET
    if request.method == 'GET' and request.GET.get('course'):
        get_course_id = request.GET.get('course')
        get_date_str = request.GET.get('date', '').strip()
        try:
            selected_course = Course.objects.get(
                id=get_course_id, instructor=teacher)
            # Parse date if provided
            if get_date_str:
                try:
                    # keep selected_date as a date object for template/JS reliability
                    date_obj = datetime.strptime(
                        get_date_str, '%Y-%m-%d').date()
                    selected_date = date_obj
                except ValueError:
                    date_obj = None
            else:
                date_obj = None

            # Build enrollments list for display
            base_enrollments = Enrollment.objects.filter(
                course=selected_course, is_active=True).order_by('student__first_name', 'student__last_name')
            enrollments = []
            for enrollment in base_enrollments:
                enrollment_data = {
                    'enrollment': enrollment,
                    'student_name': enrollment.student.get_full_name(),
                    'student_email': enrollment.student.email,
                    'current_attendance': None,
                    'previous_attendance': None,
                }
                if date_obj:
                    try:
                        prev_attendance = Attendance.objects.get(
                            enrollment=enrollment, date=date_obj)
                        enrollment_data['current_attendance'] = prev_attendance.status
                        enrollment_data['previous_attendance'] = prev_attendance.status
                    except Attendance.DoesNotExist:
                        enrollment_data['current_attendance'] = None
                        enrollment_data['previous_attendance'] = None
                enrollments.append(enrollment_data)
        except Course.DoesNotExist:
            messages.error(
                request, 'Selected course not found or you are not the instructor.')
            selected_course = None
            enrollments = None

    # Ensure selected_date is passed to template as a string in YYYY-MM-DD for display
    # The template uses the date filter, but if selected_date is a date object this will render correctly.
    context = {
        'form': form,
        'page_title': 'Mark Attendance',
        'selected_course': selected_course,
        'selected_date': selected_date,
        'enrollments': enrollments,
    }
    return render(request, 'app1/teacher/mark_attendance.html', context)


@role_required(['teacher'])
def view_attendance_course(request, course_id):
    """View attendance records for a course"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    enrollments = Enrollment.objects.filter(
        course=course, is_active=True).prefetch_related('attendance_records')

    attendance_data = []
    for enrollment in enrollments:
        total_classes = enrollment.attendance_records.count()
        present_count = enrollment.attendance_records.filter(
            status='present').count()
        absent_count = enrollment.attendance_records.filter(
            status='absent').count()

        attendance_data.append({
            'student': enrollment.student,
            'enrollment': enrollment,
            'percentage': enrollment.get_attendance_percentage(),
            'total_classes': total_classes,
            'present_count': present_count,
            'absent_count': absent_count,
            'records': enrollment.attendance_records.order_by('-date')[:10],
        })

    context = {
        'course': course,
        'attendance_data': attendance_data,
        'page_title': f'Attendance - {course.code}',
    }
    return render(request, 'app1/teacher/view_attendance.html', context)


@role_required(['student'])
def view_attendance_student(request):
    """View personal attendance"""
    student = request.user
    enrollments = Enrollment.objects.filter(student=student, is_active=True)

    attendance_data = []
    for enrollment in enrollments:
        attendance_data.append({
            'course': enrollment.course,
            'enrollment': enrollment,
            'percentage': enrollment.get_attendance_percentage(),
            'is_low': enrollment.get_attendance_percentage() < 75,
        })

    context = {
        'attendance_data': attendance_data,
        'page_title': 'My Attendance',
    }
    return render(request, 'app1/student/view_attendance.html', context)


@role_required(['student'])
def view_course_attendance_detail(request, enrollment_id):
    """View detailed attendance records for a specific course"""
    student = request.user
    enrollment = get_object_or_404(
        Enrollment, id=enrollment_id, student=student, is_active=True)

    # Get all attendance records for this enrollment, sorted by date descending
    attendance_records = Attendance.objects.filter(
        enrollment=enrollment
    ).order_by('-date')

    # Calculate summary stats
    total_classes = attendance_records.count()
    present_count = attendance_records.filter(status='present').count()
    absent_count = attendance_records.filter(status='absent').count()
    attendance_percentage = enrollment.get_attendance_percentage()

    context = {
        'enrollment': enrollment,
        'course': enrollment.course,
        'attendance_records': attendance_records,
        'total_classes': total_classes,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage,
        'page_title': f'Attendance - {enrollment.course.code}',
    }
    return render(request, 'app1/student/view_course_attendance_detail.html', context)


# ==================== Marks Views ====================

@role_required(['teacher'])
@role_required(['teacher'])
def enter_marks(request):
    """Enter marks for students - supports multiple entries per component"""
    teacher = request.user
    courses = Course.objects.filter(instructor=teacher, is_active=True)

    selected_course = None
    selected_component = None
    enrollments_data = None
    full_marks = request.POST.get(
        'full_marks', 100) if request.method == 'POST' else 100

    if request.method == 'POST':
        action = request.POST.get('action', 'load')
        course_id = request.POST.get('course')
        component = request.POST.get('component')
        full_marks_str = request.POST.get('full_marks', '100').strip()

        # Validate full_marks
        try:
            full_marks = float(full_marks_str) if full_marks_str else 100
            if full_marks <= 0:
                messages.error(request, "Full marks must be greater than 0.")
                full_marks = 100
        except ValueError:
            messages.error(request, "Full marks must be a valid number.")
            full_marks = 100

        if course_id and component:
            selected_course = get_object_or_404(
                Course, id=course_id, instructor=teacher)
            selected_component = component

            if action == 'load':
                # Load students with existing marks for this component
                enrollments = Enrollment.objects.filter(
                    course=selected_course, is_active=True).order_by('student__first_name', 'student__last_name')

                enrollments_data = []
                for enrollment in enrollments:
                    # Get all previous marks for this component
                    previous_marks = Marks.objects.filter(
                        enrollment=enrollment, component=component).order_by('component_number')

                    enrollment_data = {
                        'enrollment': enrollment,
                        'student_name': enrollment.student.get_full_name(),
                        'student_email': enrollment.student.email,
                        'previous_marks': list(previous_marks),
                        'next_entry_number': previous_marks.count() + 1 if previous_marks.exists() else 1,
                    }
                    enrollments_data.append(enrollment_data)

            elif action == 'save':
                # Save new marks entry for each student
                enrollments = Enrollment.objects.filter(
                    course=selected_course, is_active=True)

                saved_count = 0
                for enrollment in enrollments:
                    marks_obtained = request.POST.get(
                        f'marks_{enrollment.id}', '').strip()
                    if marks_obtained:
                        try:
                            marks_obtained = float(marks_obtained)
                            # Validate marks not negative
                            if marks_obtained < 0:
                                continue
                            # Validate marks not exceeding full marks
                            if marks_obtained > full_marks:
                                continue

                            # Get next component number for this enrollment
                            latest_mark = Marks.objects.filter(
                                enrollment=enrollment, component=component).order_by('-component_number').first()
                            next_number = (
                                latest_mark.component_number + 1) if latest_mark else 1

                            # Create new marks entry
                            marks_obj = Marks.objects.create(
                                enrollment=enrollment,
                                component=component,
                                component_number=next_number,
                                marks_obtained=marks_obtained,
                                full_marks=full_marks,
                                entered_by=teacher
                            )

                            # Update student result
                            update_student_result(enrollment)
                            saved_count += 1
                        except (ValueError, Marks.DoesNotExist):
                            pass

                if saved_count > 0:
                    messages.success(
                        request, f"Marks saved for {saved_count} student(s)!")
                    return redirect('enter_marks')
                else:
                    messages.warning(request, "No marks were entered.")

    context = {
        'courses': courses,
        'selected_course': selected_course,
        'selected_component': selected_component,
        'enrollments_data': enrollments_data,
        'full_marks': full_marks,
        'page_title': 'Enter Marks',
    }
    return render(request, 'app1/teacher/enter_marks.html', context)


@role_required(['student'])
def view_marks(request):
    """View personal marks and grades - displays all component entries dynamically"""
    student = request.user
    enrollments = Enrollment.objects.filter(
        student=student, is_active=True).select_related('course')

    marks_data = []
    for enrollment in enrollments:
        result = StudentResult.objects.filter(enrollment=enrollment).first()

        # Group marks by component to show multiple entries
        components = {}
        all_marks = Marks.objects.filter(enrollment=enrollment).order_by(
            'component', 'component_number')

        for mark in all_marks:
            if mark.component not in components:
                components[mark.component] = []
            components[mark.component].append({
                'number': mark.component_number,
                'marks': mark.marks_obtained,
                'full_marks': mark.full_marks,
                'percentage': mark.percentage,
            })

        # Only include result if all evaluations are complete
        has_all_evals = result and result.has_all_evaluations() if result else False

        marks_data.append({
            'course': enrollment.course,
            'enrollment': enrollment,
            'result': result if has_all_evals else None,
            'components': components,  # Changed from 'marks' to 'components'
            'has_all_evaluations': has_all_evals,
            'scheme': enrollment.course.grading_scheme if enrollment.course.grading_scheme else None,
        })

    context = {
        'marks_data': marks_data,
        'page_title': 'My Marks & Grades',
    }
    return render(request, 'app1/student/view_marks.html', context)


@role_required(['teacher'])
def configure_grading(request, course_id):
    """Configure grading scheme for a course"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    grading_scheme, created = GradingScheme.objects.get_or_create(
        course=course)

    if request.method == 'POST':
        form = GradingSchemeForm(request.POST, instance=grading_scheme)
        if form.is_valid():
            form.save()
            messages.success(request, "Grading scheme updated successfully!")
            return redirect('dashboard')
    else:
        form = GradingSchemeForm(instance=grading_scheme)

    context = {
        'form': form,
        'course': course,
        'page_title': f'Grading Scheme - {course.code}',
    }
    return render(request, 'app1/teacher/configure_grading.html', context)


# ==================== Helper Functions ====================

def check_and_send_attendance_notifications(course):
    """Check attendance and send notifications for low attendance"""
    threshold = 75
    enrollments = Enrollment.objects.filter(course=course, is_active=True)

    for enrollment in enrollments:
        attendance_pct = enrollment.get_attendance_percentage()

        if attendance_pct > 0 and attendance_pct < threshold:
            # Check if we already sent a notification
            existing = AttendanceNotification.objects.filter(
                student=enrollment.student,
                course=course
            ).exists()

            if not existing:
                # Send notification
                send_attendance_notification(
                    enrollment.student, course, attendance_pct)


def send_attendance_notification(student, course, attendance_pct):
    """Send email notification for low attendance"""
    try:
        subject = f"Low Attendance Alert - {course.code}"
        message = f"""
Dear {student.get_full_name()},

Your attendance in {course.name} ({course.code}) has fallen below 75%.

Please contact your instructor for more information.

Best regards,

Student Academic Suite
        """

        # Send to student
        send_mail(
            subject,
            message,
            'admin@universitysystem.com',
            [student.email],
            fail_silently=True
        )

        # Send to parent if email is provided
        if student.profile.parent_email:
            parent_message = f"""
Dear Parent/Guardian,

This is to inform you that your child, {student.get_full_name()}, has low attendance in {course.name} ({course.code}).

Please ensure they attend classes regularly.

Best regards,

Student Academic Suite
            """
            send_mail(
                f"Student Attendance Alert - {student.get_full_name()}",
                parent_message,
                'admin@universitysystem.com',
                [student.profile.parent_email],
                fail_silently=True
            )

        # Log notification
        AttendanceNotification.objects.create(
            student=student,
            course=course,
            attendance_percentage=attendance_pct,
            sent_to_student=True,
            sent_to_parent=bool(student.profile.parent_email)
        )
    except Exception as e:
        print(f"Error sending notification: {e}")


def update_student_result(enrollment):
    """Update student result based on all marks entries (supports multiple entries per component)"""
    result, created = StudentResult.objects.get_or_create(
        enrollment=enrollment)

    # Calculate average percentage for each component
    assignment_avg = result.calculate_component_average('assignment')
    quiz_avg = result.calculate_component_average('quiz')
    midterm_avg = result.calculate_component_average('midterm')
    final_avg = result.calculate_component_average('final')

    # Store component averages
    result.assignment_marks = Decimal(str(assignment_avg))
    result.quiz_marks = Decimal(str(quiz_avg))
    result.midterm_marks = Decimal(str(midterm_avg))
    result.final_marks = Decimal(str(final_avg))

    # Calculate grade if all evaluations are present
    if result.has_all_evaluations():
        result.calculate_grade()
    else:
        result.grade = ''  # Clear grade if not all evaluations present

    result.save()


@login_required(login_url='login')
def profile_view(request):
    """View user profile"""
    context = {
        'user': request.user,
        'profile': request.user.profile,
    }
    return render(request, 'app1/profile.html', context)


@login_required(login_url='login')
def edit_profile(request):
    """Edit user profile - Students & Teachers can only change password, Admin can edit everything"""
    user_role = request.user.profile.role

    # Check if user is editing their own profile (all roles) or admin editing someone else
    user_to_edit = request.user
    user_id = request.GET.get('user_id')

    # Admin can edit other users' profiles
    if user_id and user_role == 'admin':
        user_to_edit = get_object_or_404(User, id=user_id)
    elif user_id and user_role != 'admin':
        # Non-admin cannot edit other profiles
        messages.error(
            request, "You don't have permission to edit other profiles.")
        return redirect('profile_view')

    # Students and Teachers can only change password (when editing own profile)
    if user_role in ['student', 'teacher'] and user_to_edit.id == request.user.id:
        if request.method == 'POST':
            password_form = PasswordChangeForm(request.POST)

            if password_form.is_valid():
                password = password_form.cleaned_data.get('password')

                if password:
                    user_to_edit.set_password(password)
                    user_to_edit.save()
                    messages.success(request, "Password changed successfully!")
                    return redirect('profile_view')
                else:
                    messages.info(
                        request, "No password entered. Profile unchanged.")
                    return redirect('profile_view')
        else:
            password_form = PasswordChangeForm()

        context = {
            'password_form': password_form,
            'is_restricted_user': True,
            'user': user_to_edit,
        }
        return render(request, 'app1/edit_profile.html', context)

    # Admin can edit all fields (including their own)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user_to_edit)
        profile_form = UserProfileForm(
            request.POST, instance=user_to_edit.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            password = user_form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully!")

            # If admin changed their own password, log them out and redirect to login
            if user_to_edit.id == request.user.id and password:
                logout(request)
                messages.info(
                    request, "Password changed. Please log in with your new password.")
                return redirect('login')

            # Redirect back regardless of password change (non-password change case)
            return redirect('profile_view')
        else:
            # If forms are invalid, show errors
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"User - {field}: {error}")
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, f"Profile - {field}: {error}")
    else:
        user_form = UserForm(instance=user_to_edit)
        profile_form = UserProfileForm(instance=user_to_edit.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'is_restricted_user': False,
        'user': user_to_edit,
    }
    return render(request, 'app1/edit_profile.html', context)


# ==================== Student Registration Views ====================

def register_student(request):
    """Student self-registration page"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            # Generate unique verification token
            registration.verification_token = secrets.token_urlsafe(32)
            registration.save()

            # Send verification email
            verification_link = request.build_absolute_uri(
                f'/verify-email/{registration.verification_token}/'
            )
            # Build the email body. Include a development note only when using the console backend.
            dev_note = ''
            try:
                backend = settings.EMAIL_BACKEND
            except Exception:
                backend = ''

            if 'console' in backend:
                dev_note = (
                    "\n\nNOTE: The system is running in development mode. "
                    "Emails are printed to the console instead of being sent to an inbox. "
                    "If you do not receive an email, check the Django runserver terminal output for the verification link.\n"
                )

            message_body = f"""
Hello {registration.first_name},

Thank you for registering as a student. Please verify your email by clicking the link below:

{verification_link}

This link will expire in 24 hours.
{dev_note}
Best regards,

Student Academic Suite
            """

            try:
                send_mail(
                    subject='Verify Your Student Registration',
                    message=message_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[registration.email],
                    fail_silently=False,
                )
            except Exception as e:
                # Log the error to console; in production you may want to log this to a monitoring system
                print(f"Email sending error: {e}")

            messages.success(
                request,
                f'Registration successful! A verification link has been sent to {registration.email}. Please check your email to verify your account.'
            )
            return redirect('login')
    else:
        form = StudentRegistrationForm()

    context = {'form': form}
    return render(request, 'app1/register.html', context)


def verify_email(request, token):
    """Verify student registration email"""
    try:
        registration = StudentRegistration.objects.get(
            verification_token=token)

        if registration.is_verified:
            messages.info(request, 'This email has already been verified.')
            return redirect('login')

        registration.mark_verified()
        # Notify admins by email that a new registration has been verified
        try:
            admin_emails = list(User.objects.filter(
                profile__role='admin').values_list('email', flat=True))
            if admin_emails:
                send_mail(
                    subject='Student Registration Verified',
                    message=f"""
Hello,

The following student registration has been verified and is awaiting admin approval:

Name: {registration.first_name} {registration.last_name}
Email: {registration.email}
Registered At: {registration.created_at}

Please review and create the student account in the admin panel.
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=True,
                )
        except Exception as e:
            print(f"Error notifying admins about verified registration: {e}")

        messages.success(
            request,
            f'Email verified successfully! An administrator will create your account shortly. You will be notified at {registration.email} when your account is ready.'
        )
    except StudentRegistration.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')

    return redirect('login')


@role_required(['admin'])
def manage_student_registrations(request):
    """Admin view to manage pending student registrations"""
    # Filter by verification status
    # Default to showing all so admins can immediately see verified registrations
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    if status_filter == 'verified':
        registrations = StudentRegistration.objects.filter(is_verified=True)
    elif status_filter == 'pending':
        registrations = StudentRegistration.objects.filter(is_verified=False)
    else:
        registrations = StudentRegistration.objects.all()

    if search_query:
        registrations = registrations.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    context = {
        'registrations': registrations,
        'status_filter': status_filter,
        'search_query': search_query,
        'registrations_count': registrations.count(),
    }
    return render(request, 'app1/admin/manage_registrations.html', context)


@role_required(['admin'])
def approve_student_registration(request, registration_id):
    """Admin approves a student registration and creates user account"""
    registration = get_object_or_404(StudentRegistration, id=registration_id)
    # Prepare defaults for GET display
    default_username = f"{registration.first_name}.{registration.last_name}".lower(
    ).replace(' ', '')
    default_email = registration.email

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validation
        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            return redirect('approve_student_registration', registration_id=registration_id)

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('approve_student_registration', registration_id=registration_id)

        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            return redirect('approve_student_registration', registration_id=registration_id)

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return redirect('approve_student_registration', registration_id=registration_id)

        # Create user account
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=registration.first_name,
            last_name=registration.last_name,
            password=password
        )

        # Create profile
        UserProfile.objects.create(
            user=user,
            role='student',
            phone=registration.phone,
            parent_email=registration.parent_email,
            is_active=True
        )

        # Send welcome email with credentials
        try:
            send_mail(
                subject='Welcome! Your Student Account is Ready',
                message=f"""
Hello {registration.first_name} {registration.last_name},

Congratulations! Your student account has been approved and is now ready to use.

YOUR LOGIN CREDENTIALS:

Username: {username}
Password: {password}
Email: {email}


LOG IN HERE: http://AcademicSuite.pythonanywhere.com/login/

IMPORTANT:
1. Save your username and password in a safe place
2. After logging in, go to your profile and change your password
3. Keep your login credentials confidential

If you have any questions or issues logging in, please contact the administration.

Best regards,

Student Academic Suite Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending credentials email: {e}")

        messages.success(
            request,
            f'Student account for {user.get_full_name()} has been created successfully! Credentials have been sent to {email}.'
        )
        # Remove the temporary registration to avoid duplicates
        try:
            registration.delete()
        except Exception:
            pass

        return redirect('manage_student_registrations')

    context = {
        'registration': registration,
        'page_title': f'Approve Registration - {registration.first_name} {registration.last_name}',
        'initial_username': default_username,
        'initial_email': default_email,
    }
    return render(request, 'app1/admin/approve_registration.html', context)


@role_required(['admin'])
def reject_student_registration(request, registration_id):
    """Admin rejects a student registration"""
    registration = get_object_or_404(StudentRegistration, id=registration_id)

    if request.method == 'POST':
        reason = request.POST.get('reason', 'No reason provided.')

        # Send rejection email
        send_mail(
            subject='Your Student Registration Has Been Rejected',
            message=f"""
Hello {registration.first_name} {registration.last_name},

Unfortunately, your student registration has been rejected.

Reason: {reason}

If you believe this is in error, please contact the administration for more information.

Best regards,

Student Academic Suite
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.email],
            fail_silently=False,
        )

        # Delete registration
        registration.delete()

        messages.success(
            request, 'Registration has been rejected and the student has been notified.')
        return redirect('manage_student_registrations')

    context = {
        'registration': registration,
        'page_title': f'Reject Registration - {registration.first_name} {registration.last_name}',
    }
    return render(request, 'app1/admin/reject_registration.html', context)
