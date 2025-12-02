from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import (
    UserProfile, Course, Enrollment, Attendance,
    Marks, GradingScheme, StudentResult, AttendanceNotification, StudentRegistration
)


class LoginForm(forms.Form):
    """Custom login form"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'id': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'password'
        })
    )


class UserForm(forms.ModelForm):
    """User creation and update form"""
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Leave blank to keep current password'
        })
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and password != confirm_password:
            raise ValidationError("Passwords do not match!")

        return cleaned_data

    def clean_username(self):
        """Allow keeping the existing username unchanged"""
        username = self.cleaned_data.get('username')
        # If this is an update and username hasn't changed, allow it
        if self.instance and self.instance.pk and username == self.instance.username:
            return username
        # Otherwise validate for uniqueness
        if User.objects.filter(username=username).exclude(pk=self.instance.pk if self.instance and self.instance.pk else None).exists():
            raise ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        """Override save to exclude confirm_password from saving and handle username correctly"""
        instance = super().save(commit=False)
        # The password is handled separately in the view
        if commit:
            instance.save()
        return instance


class UserProfileForm(forms.ModelForm):
    """User profile form for additional information"""
    class Meta:
        model = UserProfile
        fields = ['phone', 'parent_email']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number',
                'type': 'tel'
            }),
            'parent_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Parent Email (for student notifications)'
            }),
        }


class PasswordChangeForm(forms.Form):
    """Form for students to change password only"""
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Leave blank to keep current password'
        })
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and password != confirm_password:
            raise ValidationError("Passwords do not match!")

        return cleaned_data


class CourseForm(forms.ModelForm):
    """Course creation and update form"""
    class Meta:
        model = Course
        fields = ['code', 'name', 'description',
                  'instructor', 'credits', 'semester', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Course Code (e.g., CS101)',
                'maxlength': '10'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Course Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Course Description',
                'rows': 4
            }),
            'instructor': forms.Select(attrs={
                'class': 'form-control'
            }),
            'credits': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
            'semester': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Fall 2024'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class EnrollmentForm(forms.ModelForm):
    """Student enrollment form"""
    class Meta:
        model = Enrollment
        fields = ['student', 'course', 'is_active']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control'
            }),
            'course': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class AttendanceForm(forms.ModelForm):
    """Attendance marking form for a single record"""
    class Meta:
        model = Attendance
        fields = ['status']
        widgets = {
            'status': forms.RadioSelect(choices=[
                ('present', 'Present'),
                ('absent', 'Absent')
            ], attrs={
                'class': 'form-check-input'
            }),
        }


class AttendanceBulkForm(forms.Form):
    """Bulk attendance marking form for multiple students"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Attendance Date'
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    def __init__(self, teacher=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(
                instructor=teacher, is_active=True)


class MarksForm(forms.ModelForm):
    """Marks entry form"""
    class Meta:
        model = Marks
        fields = ['component', 'marks_obtained', 'full_marks']
        widgets = {
            'component': forms.Select(attrs={
                'class': 'form-control'
            }),
            'marks_obtained': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Marks Obtained',
                'step': '0.01',
                'min': '0'
            }),
            'full_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Marks',
                'step': '0.01',
                'value': '100',
                'min': '0'
            }),
        }


class GradingSchemeForm(forms.ModelForm):
    """Grading scheme configuration form"""
    class Meta:
        model = GradingScheme
        fields = ['assignment_percentage', 'quiz_percentage',
                  'midterm_percentage', 'final_percentage']
        widgets = {
            'assignment_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'placeholder': 'Assignment %'
            }),
            'quiz_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'placeholder': 'Quiz %'
            }),
            'midterm_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'placeholder': 'Midterm %'
            }),
            'final_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'placeholder': 'Final %'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = (
            cleaned_data.get('assignment_percentage', 0) +
            cleaned_data.get('quiz_percentage', 0) +
            cleaned_data.get('midterm_percentage', 0) +
            cleaned_data.get('final_percentage', 0)
        )

        if total != 100:
            raise ValidationError(
                f"Percentages must add up to 100%. Current total: {total}%")

        return cleaned_data


class StudentResultForm(forms.ModelForm):
    """Student result form for entering all marks at once"""
    class Meta:
        model = StudentResult
        fields = ['assignment_marks', 'quiz_marks',
                  'midterm_marks', 'final_marks']
        widgets = {
            'assignment_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Assignment Marks'
            }),
            'quiz_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Quiz Marks'
            }),
            'midterm_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Midterm Marks'
            }),
            'final_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Final Marks'
            }),
        }


class StudentRegistrationForm(forms.ModelForm):
    """Form for student self-registration"""
    class Meta:
        model = StudentRegistration
        fields = ['email', 'first_name', 'last_name', 'phone', 'parent_email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email Address',
                'required': True
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number',
                'type': 'tel'
            }),
            'parent_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Parent Email (optional)'
            }),
        }

    def clean_email(self):
        """Check if email is not already registered"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "This email is already registered. Please log in or use a different email.")
        if StudentRegistration.objects.filter(email=email, is_verified=True).exists():
            raise ValidationError(
                "This email is already verified. Please wait for admin to create your account.")
        # Delete any unverified registrations with same email (allow retry)
        StudentRegistration.objects.filter(
            email=email, is_verified=False).delete()
        return email
