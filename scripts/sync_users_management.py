#!/usr/bin/env python
"""
fitbit_users 테이블에서 새로운 사용자를 감지하여
fitbit_users_m 테이블로 복사하는 스크립트
매시간 정각에 실행됨
"""
import os
import sys
import django
from datetime import datetime

# Django 환경 설정
sys.path.append('/home/sehnr_kdca1885/myhealth-app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhealth.settings')
django.setup()

# Django 모델 import
from fitbit.models import FitbitUser, FitbitUserManagement


def log_message(message):
    """로그 메시지 출력 (시간 포함)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")


def sync_new_users():
    """새로운 사용자만 fitbit_users_m 테이블로 동기화"""
    log_message("=== fitbit_users_m 테이블 동기화 시작 (신규 사용자만) ===")

    # fitbit_users에서 모든 사용자 가져오기
    all_users = FitbitUser.objects.all()

    # fitbit_users_m에 있는 사용자 ID 목록
    existing_user_ids = set(
        FitbitUserManagement.objects.values_list('fitbit_user_id', flat=True)
    )

    new_users_count = 0

    for user in all_users:
        if user.fitbit_user_id not in existing_user_ids:
            # 새로운 사용자만 추가 (기존 사용자는 절대 업데이트하지 않음)
            FitbitUserManagement.objects.create(
                fitbit_user_id=user.fitbit_user_id,
                full_name=user.full_name,
                display_name=user.display_name,
                gender=user.gender,
                age=user.age,
                date_of_birth=user.date_of_birth,
                height=user.height,
                weight=user.weight,
                avatar_url=user.avatar_url,
                member_since=user.member_since,
                profile_synced_at=user.profile_synced_at,
            )
            log_message(f"[신규] {user.fitbit_user_id} - {user.full_name} 추가됨")
            new_users_count += 1

    log_message(
        f"=== 동기화 완료 - 신규 사용자: {new_users_count}명 ==="
    )


if __name__ == '__main__':
    sync_new_users()
