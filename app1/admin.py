from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserProfile, Course, Enrollment, Attendance,
    Marks, GradingScheme, StudentResult, AttendanceNotification, StudentRegistration
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_full_name', 'role', 'is_active', 'phone']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['user__username',
                     'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role')
        }),
        ('Contact Information', {
            'fields': ('phone', 'parent_email')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_full_name.short_description = 'Name'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'instructor_name',
                    'semester', 'credits', 'is_active', 'student_count']
    list_filter = ['is_active', 'semester', 'created_at']
    search_fields = ['code', 'name',
                     'instructor__first_name', 'instructor__last_name']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Course Information', {
            'fields': ('code', 'name', 'description', 'instructor')
        }),
        ('Details', {
            'fields': ('credits', 'semester', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def instructor_name(self, obj):
        return obj.instructor.get_full_name() if obj.instructor else 'Unassigned'
    instructor_name.short_description = 'Instructor'

    def student_count(self, obj):
        return obj.enrollments.filter(is_active=True).count()
    student_count.short_description = 'Students'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'course_code',
                    'enrollment_date', 'is_active', 'attendance_percentage']
    list_filter = ['is_active', 'enrolled_date', 'course__semester']
    search_fields = ['student__username', 'student__first_name',
                     'student__last_name', 'course__code']
    readonly_fields = ['enrolled_date', 'attendance_percentage']
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'course', 'is_active')
        }),
        ('Statistics', {
            'fields': ('attendance_percentage', 'enrolled_date'),
            'classes': ('collapse',)
        }),
    )

    def student_name(self, obj):
        return obj.student.get_full_name()
    student_name.short_description = 'Student'

    def course_code(self, obj):
        return obj.course.code
    course_code.short_description = 'Course'

    def enrollment_date(self, obj):
        return obj.enrolled_date.strftime('%Y-%m-%d')
    enrollment_date.short_description = 'Enrolled'

    def attendance_percentage(self, obj):
        percentage = obj.get_attendance_percentage()
        color = '#22C55E' if percentage >= 75 else '#EF4444'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            percentage
        )
    attendance_percentage.short_description = 'Attendance'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'course_code',
                    'date', 'status_badge', 'marked_by_name']
    list_filter = ['status', 'date', 'enrollment__course__code']
    search_fields = ['enrollment__student__username',
                     'enrollment__course__code']
    date_hierarchy = 'date'
    readonly_fields = ['marked_at']
    fieldsets = (
        ('Attendance Record', {
            'fields': ('enrollment', 'date', 'status')
        }),
        ('Marked By', {
            'fields': ('marked_by', 'marked_at'),
        }),
    )

    def student_name(self, obj):
        return obj.enrollment.student.get_full_name()
    student_name.short_description = 'Student'

    def course_code(self, obj):
        return obj.enrollment.course.code
    course_code.short_description = 'Course'

    def status_badge(self, obj):
        color = '#22C55E' if obj.status == 'present' else '#EF4444'
        label = '✓ Present' if obj.status == 'present' else '✗ Absent'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            label
        )
    status_badge.short_description = 'Status'

    def marked_by_name(self, obj):
        return obj.marked_by.get_full_name() if obj.marked_by else 'Unknown'
    marked_by_name.short_description = 'Marked By'


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'course_code', 'component',
                    'marks_obtained', 'percentage', 'entered_by_name']
    list_filter = ['component', 'enrollment__course__code']
    search_fields = ['enrollment__student__username',
                     'enrollment__course__code']
    readonly_fields = ['percentage', 'entered_at']
    fieldsets = (
        ('Marks Information', {
            'fields': ('enrollment', 'component', 'marks_obtained', 'full_marks', 'percentage')
        }),
        ('Entry Information', {
            'fields': ('entered_by', 'entered_at'),
        }),
    )

    def student_name(self, obj):
        return obj.enrollment.student.get_full_name()
    student_name.short_description = 'Student'

    def course_code(self, obj):
        return obj.enrollment.course.code
    course_code.short_description = 'Course'

    def entered_by_name(self, obj):
        return obj.entered_by.get_full_name() if obj.entered_by else 'Unknown'
    entered_by_name.short_description = 'Entered By'


@admin.register(GradingScheme)
class GradingSchemeAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'assignment_percentage', 'quiz_percentage',
                    'midterm_percentage', 'final_percentage', 'is_valid_display']
    readonly_fields = ['course']
    fieldsets = (
        ('Course', {
            'fields': ('course',)
        }),
        ('Grading Percentages', {
            'fields': ('assignment_percentage', 'quiz_percentage', 'midterm_percentage', 'final_percentage'),
            'description': 'All percentages must add up to 100%'
        }),
    )

    def course_code(self, obj):
        return obj.course.code
    course_code.short_description = 'Course'

    def is_valid_display(self, obj):
        is_valid = obj.is_valid()
        color = '#22C55E' if is_valid else '#EF4444'
        label = '✓ Valid' if is_valid else '✗ Invalid'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            label
        )
    is_valid_display.short_description = 'Valid'

    def has_delete_permission(self, request):
        return False


@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'course_code',
                    'total_marks', 'grade_badge', 'calculated_at']
    list_filter = ['grade', 'calculated_at']
    search_fields = ['enrollment__student__username',
                     'enrollment__course__code']
    date_hierarchy = 'calculated_at'
    readonly_fields = ['total_marks', 'grade', 'calculated_at']
    fieldsets = (
        ('Student & Course', {
            'fields': ('enrollment',)
        }),
        ('Component Marks', {
            'fields': ('assignment_marks', 'quiz_marks', 'midterm_marks', 'final_marks')
        }),
        ('Result', {
            'fields': ('total_marks', 'grade', 'calculated_at'),
        }),
    )

    def student_name(self, obj):
        return obj.enrollment.student.get_full_name()
    student_name.short_description = 'Student'

    def course_code(self, obj):
        return obj.enrollment.course.code
    course_code.short_description = 'Course'

    def grade_badge(self, obj):
        grade_colors = {
            'A': '#22C55E',
            'B': '#3B82F6',
            'C': '#F59E0B',
            'D': '#F97316',
            'F': '#EF4444',
        }
        color = grade_colors.get(obj.grade, '#64748B')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.grade or 'N/A'
        )
    grade_badge.short_description = 'Grade'

    def has_delete_permission(self, request):
        return False


@admin.register(AttendanceNotification)
class AttendanceNotificationAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'course_code',
                    'attendance_percentage', 'sent_badge', 'sent_at']
    list_filter = ['sent_at', 'sent_to_parent', 'sent_to_student']
    search_fields = ['student__username', 'course__code']
    date_hierarchy = 'sent_at'
    readonly_fields = ['student', 'course', 'attendance_percentage', 'sent_at']
    fieldsets = (
        ('Notification Details', {
            'fields': ('student', 'course', 'attendance_percentage')
        }),
        ('Recipients', {
            'fields': ('sent_to_student', 'sent_to_parent')
        }),
        ('Timestamp', {
            'fields': ('sent_at',),
        }),
    )

    def student_name(self, obj):
        return obj.student.get_full_name()
    student_name.short_description = 'Student'

    def course_code(self, obj):
        return obj.course.code
    course_code.short_description = 'Course'

    def sent_badge(self, obj):
        badges = []
        if obj.sent_to_student:
            badges.append(
                '<span style="background-color: #3B82F6; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 4px;">Student</span>')
        if obj.sent_to_parent:
            badges.append(
                '<span style="background-color: #F59E0B; color: white; padding: 2px 6px; border-radius: 3px;">Parent</span>')
        return format_html(''.join(badges))
    sent_badge.short_description = 'Sent To'

    def has_delete_permission(self, request):
        return False


@admin.register(StudentRegistration)
class StudentRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'email', 'status_badge', 'phone', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    readonly_fields = ['verification_token', 'created_at', 'verified_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'parent_email')
        }),
        ('Verification Status', {
            'fields': ('is_verified', 'verification_token', 'verified_at', 'created_at')
        }),
    )

    def student_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    student_name.short_description = 'Student Name'

    def status_badge(self, obj):
        color = '#22C55E' if obj.is_verified else '#F59E0B'
        label = '✓ Verified' if obj.is_verified else '⏳ Pending'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            label
        )
    status_badge.short_description = 'Status'

    def has_delete_permission(self, request):
        return False
