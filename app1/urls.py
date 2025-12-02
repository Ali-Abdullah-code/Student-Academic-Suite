from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_student, name="register_student"),
    path("verify-email/<str:token>/", views.verify_email, name="verify_email"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # Profile
    path("profile/", views.profile_view, name="profile_view"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),

    # Admin - User Management
    path("manage/users/", views.manage_users, name="manage_users"),
    path("manage/users/add/", views.add_user, name="add_user"),
    path("manage/users/edit/<int:user_id>/",
         views.edit_user, name="edit_user"),
    path("manage/users/deactivate/<int:user_id>/",
         views.deactivate_user, name="deactivate_user"),
    path("manage/users/activate/<int:user_id>/",
         views.activate_user, name="activate_user"),
    path("manage/users/delete/<int:user_id>/",
         views.delete_user, name="delete_user"),

    # Admin - Student Registration Management
    path("manage/registrations/", views.manage_student_registrations,
         name="manage_student_registrations"),
    path("manage/registrations/<int:registration_id>/approve/",
         views.approve_student_registration, name="approve_student_registration"),
    path("manage/registrations/<int:registration_id>/reject/",
         views.reject_student_registration, name="reject_student_registration"),
    path("manage/registrations/<int:registration_id>/delete/",
         views.delete_student_registration, name="delete_student_registration"),

    # Admin - Course Management
    path("manage/courses/", views.manage_courses, name="manage_courses"),
    path("manage/courses/add/", views.add_course, name="add_course"),
    path("manage/courses/edit/<int:course_id>/",
         views.edit_course, name="edit_course"),
    path("manage/courses/delete/<int:course_id>/",
         views.delete_course, name="delete_course"),

    # Admin - Enrollment Management
    path("manage/enrollments/", views.manage_enrollments,
         name="manage_enrollments"),
    path("manage/enrollments/add/", views.add_enrollment, name="add_enrollment"),
    path("manage/enrollments/delete/<int:enrollment_id>/",
         views.delete_enrollment, name="delete_enrollment"),

    # Teacher - Attendance
    path("teacher/attendance/mark/", views.mark_attendance, name="mark_attendance"),
    path("teacher/attendance/view/<int:course_id>/",
         views.view_attendance_course, name="view_attendance_course"),

    # Teacher - Marks
    path("teacher/marks/enter/", views.enter_marks, name="enter_marks"),
    path("teacher/marks/grading/<int:course_id>/",
         views.configure_grading, name="configure_grading"),

    # Student - Attendance
    path("student/attendance/", views.view_attendance_student,
         name="view_attendance_student"),
    path("student/attendance/<int:enrollment_id>/", views.view_course_attendance_detail,
         name="view_course_attendance_detail"),

    # Student - Marks
    path("student/marks/", views.view_marks, name="view_marks"),
]
