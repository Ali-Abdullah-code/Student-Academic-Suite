from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta


class UserProfile(models.Model):
    """Extended user profile for role-based access"""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    parent_email = models.EmailField(
        blank=True, help_text="Parent email for student notifications")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"


class Course(models.Model):
    """Course model for different subjects"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={
                                   'profile__role': 'teacher'}, related_name='courses_teaching')
    credits = models.IntegerField(default=3)
    semester = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Enrollment(models.Model):
    """Student enrollment in courses"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={
                                'profile__role': 'student'}, related_name='enrollments')
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_date']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.code}"

    def get_attendance_percentage(self):
        """Calculate attendance percentage for a student in this course.
        Default is 100%, decreased by 1% for each absence."""
        total_classes = self.attendance_records.count()
        if total_classes == 0:
            return 100  # Default to 100% if no attendance records yet
        absent_count = self.attendance_records.filter(
            status='absent').count()
        # Calculate as 100% minus absences percentage
        return round(100 - ((absent_count / total_classes) * 100), 2)


class Attendance(models.Model):
    """Attendance tracking for students"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
    ]

    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={
                                  'profile__role': 'teacher'})
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['enrollment', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.date} ({self.status})"


class GradingScheme(models.Model):
    """Grading scheme for courses"""
    GRADE_CHOICES = [
        ('A', 'A (90-100%)'),
        ('B', 'B (80-89%)'),
        ('C', 'C (70-79%)'),
        ('D', 'D (60-69%)'),
        ('F', 'F (Below 60%)'),
    ]

    course = models.OneToOneField(
        Course, on_delete=models.CASCADE, related_name='grading_scheme')
    assignment_percentage = models.IntegerField(
        default=10, validators=[MinValueValidator(0), MaxValueValidator(100)])
    quiz_percentage = models.IntegerField(
        default=10, validators=[MinValueValidator(0), MaxValueValidator(100)])
    midterm_percentage = models.IntegerField(
        default=30, validators=[MinValueValidator(0), MaxValueValidator(100)])
    final_percentage = models.IntegerField(
        default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        verbose_name_plural = "Grading Schemes"

    def __str__(self):
        return f"Grading Scheme - {self.course.code}"

    def is_valid(self):
        """Check if percentages add up to 100"""
        total = self.assignment_percentage + self.quiz_percentage + \
            self.midterm_percentage + self.final_percentage
        return total == 100

    def save(self, *args, **kwargs):
        if not self.is_valid():
            raise ValueError("Grading scheme percentages must add up to 100%")
        super().save(*args, **kwargs)


class Marks(models.Model):
    """Marks/grades for students - supports multiple entries per component"""
    COMPONENT_CHOICES = [
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
        ('midterm', 'Midterm'),
        ('final', 'Final'),
    ]

    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name='marks')
    component = models.CharField(max_length=15, choices=COMPONENT_CHOICES)
    # Track Assignment 1, 2, 3...
    component_number = models.PositiveIntegerField(default=1)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, validators=[
                                         MinValueValidator(0)])
    full_marks = models.DecimalField(
        max_digits=5, decimal_places=2, default=100)
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    entered_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, limit_choices_to={'profile__role': 'teacher'})
    entered_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Allow multiple per component, but not duplicates
        unique_together = ['enrollment', 'component', 'component_number']
        ordering = ['enrollment', 'component', 'component_number']

    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.component} #{self.component_number} ({self.marks_obtained})"

    def save(self, *args, **kwargs):
        """Calculate percentage before saving"""
        if self.full_marks > 0:
            self.percentage = (self.marks_obtained / self.full_marks) * 100
        # Validate marks not exceeding full marks
        if self.marks_obtained > self.full_marks:
            raise ValueError(
                f"Marks obtained ({self.marks_obtained}) cannot exceed full marks ({self.full_marks})")
        super().save(*args, **kwargs)


class StudentResult(models.Model):
    """Final result for each student in a course"""
    GRADE_CHOICES = [
        ('A', 'A (90-100%)'),
        ('B', 'B (80-89%)'),
        ('C', 'C (70-79%)'),
        ('D', 'D (60-69%)'),
        ('F', 'F (Below 60%)'),
    ]

    enrollment = models.OneToOneField(
        Enrollment, on_delete=models.CASCADE, related_name='result')
    assignment_marks = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)
    quiz_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    midterm_marks = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)
    final_marks = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)
    total_marks = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)
    grade = models.CharField(max_length=1, choices=GRADE_CHOICES, blank=True)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Student Results"
        unique_together = ['enrollment']

    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.enrollment.course.code} ({self.grade})"

    def get_component_count(self, component):
        """Get count of entries for a component"""
        return Marks.objects.filter(enrollment=self.enrollment, component=component).count()

    def has_all_evaluations(self):
        """Check if at least one entry for each component (assignment, quiz, midterm, final) exists"""
        marks = Marks.objects.filter(enrollment=self.enrollment)
        components = set(marks.values_list('component', flat=True))
        required_components = {'assignment', 'quiz', 'midterm', 'final'}
        return required_components.issubset(components)

    def calculate_component_average(self, component):
        """Calculate average percentage for a component across all its entries"""
        component_marks = Marks.objects.filter(
            enrollment=self.enrollment, component=component)
        if not component_marks.exists():
            return 0
        total_percentage = sum(m.percentage for m in component_marks)
        return total_percentage / component_marks.count()

    def calculate_total(self):
        """Calculate total marks based on grading scheme with dynamic weightage

        Weightage is divided equally among multiple entries:
        - Assignments: Combined average divided equally
        - Quizzes: Combined average divided equally  
        - Midterms: 30% total, divided equally among all midterms
        - Finals: 40% total
        """
        scheme = self.enrollment.course.grading_scheme

        # Get averages for each component
        assignment_avg = self.calculate_component_average('assignment')
        quiz_avg = self.calculate_component_average('quiz')
        midterm_avg = self.calculate_component_average('midterm')
        final_marks = self.calculate_component_average(
            'final')  # Usually only 1 final

        # Calculate total with weightage
        self.total_marks = (
            (assignment_avg * scheme.assignment_percentage / 100) +
            (quiz_avg * scheme.quiz_percentage / 100) +
            (midterm_avg * scheme.midterm_percentage / 100) +
            (final_marks * scheme.final_percentage / 100)
        )
        return self.total_marks

    def calculate_grade(self):
        """Calculate grade based on total marks"""
        self.calculate_total()
        if self.total_marks >= 90:
            self.grade = 'A'
        elif self.total_marks >= 80:
            self.grade = 'B'
        elif self.total_marks >= 70:
            self.grade = 'C'
        elif self.total_marks >= 60:
            self.grade = 'D'
        else:
            self.grade = 'F'
        return self.grade


class AttendanceNotification(models.Model):
    """Track sent notifications for low attendance"""
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='attendance_notifications')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_to_student = models.BooleanField(default=True)
    sent_to_parent = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Attendance Notifications"
        ordering = ['-sent_at']

    def __str__(self):
        return f"Notification for {self.student.get_full_name()} - {self.course.code}"


class StudentRegistration(models.Model):
    """Temporary model for student self-registration pending admin approval"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    parent_email = models.EmailField(blank=True)
    verification_token = models.CharField(max_length=100, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = "✓ Verified" if self.is_verified else "✗ Pending"
        return f"{self.first_name} {self.last_name} ({self.email}) - {status}"

    def mark_verified(self):
        """Mark registration as verified"""
        from django.utils import timezone
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save()
