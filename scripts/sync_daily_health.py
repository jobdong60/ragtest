#!/usr/bin/env python
"""
모든 Fitbit 사용자의 일일 건강 데이터 동기화 스크립트
하루 1회 실행하여 수면, 호흡수, 피부 온도 데이터 수집
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Django 환경 설정
sys.path.append('/home/sehnr_kdca1885/myhealth-app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhealth.settings')
django.setup()

# Django 모델 및 함수 import
from fitbit.models import FitbitUser
from fitbit.data_sync import sync_daily_health_data
from fitbit.token_refresh import refresh_access_token


def log_message(message):
    """로그 메시지 출력 (시간 포함)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")


def sync_all_users_daily_health():
    """모든 사용자의 어제 일일 건강 데이터 동기화"""
    log_message("=== Fitbit 일일 건강 데이터 동기화 시작 ===")

    # 어제 날짜 계산
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    log_message(f"동기화 대상 날짜: {yesterday}")

    # 모든 FitbitUser 가져오기
    fitbit_users = FitbitUser.objects.all()
    total_users = fitbit_users.count()

    if total_users == 0:
        log_message("동기화할 사용자가 없습니다.")
        return

    log_message(f"총 {total_users}명의 사용자 일일 건강 데이터 동기화 시작")

    success_count = 0
    fail_count = 0

    # 각 사용자별로 동기화
    for fitbit_user in fitbit_users:
        try:
            log_message(f"[{fitbit_user.fitbit_user_id}] 동기화 시작...")

            # 토큰 갱신
            if not refresh_access_token(fitbit_user):
                log_message(f"[{fitbit_user.fitbit_user_id}] 토큰 갱신 실패 - 스킵")
                fail_count += 1
                continue

            # 어제 일일 건강 데이터 동기화
            result = sync_daily_health_data(
                fitbit_user.fitbit_user_id,
                fitbit_user.access_token,
                yesterday
            )

            if result['success']:
                log_message(
                    f"[{fitbit_user.fitbit_user_id}] 성공 - "
                    f"Sleep: {result['sleep_logs']}, "
                    f"BR: {result['breathing_rate']}, "
                    f"Temp: {result['skin_temperature']}"
                )
                success_count += 1
            else:
                log_message(
                    f"[{fitbit_user.fitbit_user_id}] 실패 - "
                    f"Error: {result.get('error', 'Unknown')}"
                )
                fail_count += 1

        except Exception as e:
            log_message(f"[{fitbit_user.fitbit_user_id}] 예외 발생: {e}")
            fail_count += 1

    log_message(
        f"=== 동기화 완료 - 성공: {success_count}, 실패: {fail_count} ==="
    )


if __name__ == '__main__':
    sync_all_users_daily_health()
