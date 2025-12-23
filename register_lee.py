import os
import django
import sys

# Setup Django environment
sys.path.append('c:/Users/cly0310/platform/fitbit-myhealth-main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhealth.settings')
django.setup()

from fitbit.models import PolarUser
from datetime import date

def create_target_user():
    try:
        # Check if already exists to avoid duplicates
        if PolarUser.objects.filter(full_name="이종민").exists():
            print("User '이종민' already exists.")
            user = PolarUser.objects.get(full_name="이종민")
            print(f"Existing User Info: {user.username}, {user.full_name}, {user.date_of_birth}")
            return

        # Create new user
        # Using a generated username since phone number wasn't provided, but I'll generate a random one or use a sensible default
        username = "user_lee_jongmin" 
        password = "password1234" 

        new_subject = PolarUser(
            username=username,
            full_name="이종민",
            phone_number="010-0000-0000", # Dummy phone
            gender="남성",
            date_of_birth=date(1997, 3, 10),
            age=30,
            height=175.0,
            weight=70.0,
            is_active=True
        )
        new_subject.set_password(password)
        new_subject.save()

        print("Successfully created '이종민'.")
        print(f"Username: {new_subject.username}")
        print(f"Full Name: {new_subject.full_name}")
        print(f"Age: {new_subject.age}")
        
    except Exception as e:
        print(f"Error creating user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_target_user()
