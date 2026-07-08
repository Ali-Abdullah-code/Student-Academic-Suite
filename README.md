# Student Academic Suite

A comprehensive web-based system for managing student attendance and academic results in educational institutions. Built with Django, this application provides role-based access for administrators, teachers, and students to streamline attendance tracking, marks entry, grade calculation, and communication.

## Features

### Core Functionality
- **User Authentication & Role-Based Access**: Secure login system with three user roles (Admin, Teacher, Student)
- **Student Self-Registration**: Email verification process for new student accounts
- **Automated Attendance Management**: Mark attendance, calculate percentages, and send low-attendance notifications
- **Academic Results Management**: Enter marks, configure grading schemes, and automatically calculate final grades
- **Course & Enrollment Management**: Admin control over courses and student enrollments

### For Administrators
- Manage user accounts (create, edit, activate/deactivate)
- Approve/reject student registration requests
- Manage courses and enrollments
- System-wide data oversight

### For Teachers
- Mark attendance for assigned courses
- Enter marks for multiple assessment components
- Configure grading schemes for courses
- View attendance reports and statistics

### For Students
- View personal attendance records and percentages
- Access detailed marksheets and final grades
- Receive email notifications for low attendance

### Additional Features
- Email notifications for low attendance (<75%) to students and parents
- Support for multiple marks entries per assessment component
- Automatic grade calculation based on configurable schemes
- Responsive web interface
- Data security with role-based permissions

## Technologies Used

- **Backend**: Django 5.1.2
- **Database**: SQLite (default), easily configurable for PostgreSQL/MySQL
- **Frontend**: HTML5, CSS3, JavaScript
- **Email**: SMTP integration for notifications
- **Authentication**: Django's built-in auth system with custom user profiles

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Ali-Abdullah-Code/Student-Academic-Suite.git
   cd Student-Academic-Suite
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv env
   # On Windows:
   env\Scripts\activate
   # On macOS/Linux:
   source env/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser** (admin account):
   ```bash
   python manage.py createsuperuser
   ```

6. **Configure email settings** (optional but recommended for notifications):
   - Set environment variables for email:
     ```bash
     # PowerShell example:
     $env:EMAIL_HOST_USER = 'your-email@gmail.com'
     $env:EMAIL_HOST_PASSWORD = 'your-app-password'
     ```
   - Or modify `StudentAcademicSuite/settings.py` directly

7. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

8. **Access the application**:
   - Open your browser and go to `http://127.0.0.1:8000`
   - Log in with the superuser credentials or register as a student

## Usage

### Initial Setup
1. Log in as admin using the superuser account
2. Create teacher accounts via Admin > User Management
3. Teachers can create courses and configure grading schemes
4. Students can self-register or be created by admins
5. Admins enroll students in courses

### Daily Operations

#### For Teachers:
1. Log in and access your dashboard
2. Mark attendance for your courses by selecting course and date
3. Enter marks for assessments (assignments, quizzes, midterms, finals)
4. Configure grading schemes if needed
5. View attendance reports

#### For Students:
1. Log in to view your dashboard
2. Check attendance percentages across courses
3. View detailed marks and grades
4. Receive email alerts for low attendance

#### For Administrators:
1. Manage all users, courses, and enrollments
2. Approve pending student registrations
3. Monitor system usage and data

## Project Structure

```
Student-Academic-Suite/
├── StudentAcademicSuite/         # Django project settings
│   ├── settings.py               # Main configuration
│   ├── urls.py                   # URL routing
│   ├── wsgi.py                   # WSGI configuration
│   └── asgi.py                   # ASGI configuration
├── app1/                         # Main Django app
│   ├── models.py                 # Database models
│   ├── views.py                  # View functions
│   ├── forms.py                  # Django forms
│   ├── urls.py                   # App URL routing
│   ├── admin.py                  # Django admin configuration
│   ├── templates/                # HTML templates
│   ├── static/                   # CSS, JS, images
│   └── migrations/               # Database migrations
├── env/                          # Virtual environment (not in repo)
├── db.sqlite3                    # SQLite database
├── manage.py                     # Django management script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Configuration

### Email Settings
The system uses SMTP for sending notifications. Configure the following in `settings.py` or via environment variables:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@universitysystem.com'
```

### Database
By default, the system uses SQLite. For production, configure PostgreSQL or MySQL in `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Testing

Run the test suite:
```bash
python manage.py test
```

## Deployment

### Production Deployment
1. Set `DEBUG = False` in settings.py
2. Configure a production database
3. Set up a web server (nginx + gunicorn recommended)
4. Use environment variables for sensitive data
5. Run `python manage.py collectstatic`

### Docker Deployment (Optional)
If you want to containerize the application:

1. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   RUN python manage.py collectstatic --noinput
   CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
   ```

2. Build and run:
   ```bash
   docker build -t student-suite .
   docker run -p 8000:8000 student-suite
   ```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add new feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

### Development Guidelines
- Follow Django best practices
- Write clear, documented code
- Test new features thoroughly
- Update documentation as needed

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions:
- Create an issue on GitHub
- Contact the development team

## Changelog

### Version 1.0.0
- Initial release with core attendance and results management
- Role-based access control
- Email notifications
- Student self-registration
- Responsive web interface

---

**Note**: This system is designed for educational institutions and should be deployed in accordance with your organization's data protection policies.</content>
