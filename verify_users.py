import os
import django
import sys

# Setup Django environment
sys.path.append('c:/Users/cly0310/platform/fitbit-myhealth-main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhealth.settings')
django.setup()

from fitbit.models import PolarUser

def list_users():
    users = PolarUser.objects.all()
    print(f"Total Users: {users.count()}")
    for user in users:
        print(f"User: {user.full_name} ({user.username}), Active: {user.is_active}")

if __name__ == "__main__":
    list_users()
