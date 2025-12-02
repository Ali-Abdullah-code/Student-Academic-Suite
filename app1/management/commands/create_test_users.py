from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app1.models import UserProfile


class Command(BaseCommand):
    help = 'Create test users for all roles'

    def handle(self, *args, **options):
        # Admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@universitysystem.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_superuser': True,
                'is_staff': True
            }
        )
        admin.set_password('password123')
        admin.save()

        admin_profile, _ = UserProfile.objects.get_or_create(
            user=admin,
            defaults={'role': 'admin', 'is_active': True}
        )
        self.stdout.write(self.style.SUCCESS('✓ Admin: admin / password123'))

        # Teacher user
        teacher, created = User.objects.get_or_create(
            username='teacher1',
            defaults={
                'email': 'teacher1@universitysystem.com',
                'first_name': 'John',
                'last_name': 'Smith',
            }
        )
        teacher.set_password('password123')
        teacher.save()

        teacher_profile, _ = UserProfile.objects.get_or_create(
            user=teacher,
            defaults={'role': 'teacher', 'is_active': True}
        )
        self.stdout.write(self.style.SUCCESS(
            '✓ Teacher: teacher1 / password123'))

        # Student user
        student, created = User.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'student1@universitysystem.com',
                'first_name': 'Alice',
                'last_name': 'Johnson',
            }
        )
        student.set_password('password123')
        student.save()

        student_profile, _ = UserProfile.objects.get_or_create(
            user=student,
            defaults={'role': 'student', 'is_active': True,
                      'parent_email': 'parent@email.com'}
        )
        self.stdout.write(self.style.SUCCESS(
            '✓ Student: student1 / password123'))

        self.stdout.write(self.style.SUCCESS(
            '\n✓ All test users created successfully!'))
