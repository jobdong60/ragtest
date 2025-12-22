#!/usr/bin/env python
"""
목요일(10/31)부터 금요일(11/1)까지의 누락된 데이터를 채우는 스크립트
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
from fitbit.data_sync import sync_fitbit_data_for_date
from fitbit.token_refresh import refresh_access_token


def log_message(message):
    """로그 메시지 출력 (시간 포함)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")


def backfill_date_range(start_date, end_date):
    """
    특정 날짜 범위의 데이터를 채움

    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
    """
    log_message(f"=== 데이터 Backfill 시작: {start_date} ~ {end_date} ===")

    # 모든 FitbitUser 가져오기
    fitbit_users = FitbitUser.objects.all()
    total_users = fitbit_users.count()

    if total_users == 0:
        log_message("백필할 사용자가 없습니다.")
        return

    log_message(f"총 {total_users}명의 사용자 데이터 백필 시작")

    # 날짜 범위 생성
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')

    dates = []
    current_dt = start_dt
    while current_dt <= end_dt:
        dates.append(current_dt.strftime('%Y-%m-%d'))
        current_dt += timedelta(days=1)

    log_message(f"백필할 날짜: {', '.join(dates)}")

    # 각 사용자별로 데이터 백필
    for fitbit_user in fitbit_users:
        log_message(f"\n[{fitbit_user.fitbit_user_id}] 백필 시작...")

        try:
            # 토큰 갱신
            if not refresh_access_token(fitbit_user):
                log_message(f"[{fitbit_user.fitbit_user_id}] 토큰 갱신 실패 - 스킵")
                continue

            # 각 날짜별로 전체 데이터 동기화
            for date in dates:
                log_message(f"[{fitbit_user.fitbit_user_id}] {date} 동기화 중...")

                result = sync_fitbit_data_for_date(
                    fitbit_user.fitbit_user_id,
                    fitbit_user.access_token,
                    date
                )

                if result['success']:
                    log_message(
                        f"[{fitbit_user.fitbit_user_id}] {date} 성공 - "
                        f"HR: {result['intraday_hr']}, "
                        f"Steps: {result['intraday_steps']}, "
                        f"Calories: {result['intraday_calories']}, "
                        f"Distance: {result['intraday_distance']}, "
                        f"Floors: {result['intraday_floors']}, "
                        f"Elevation: {result['intraday_elevation']}, "
                        f"SpO2: {result['intraday_spo2']}, "
                        f"HRV: {result['intraday_hrv']}"
                    )
                else:
                    log_message(
                        f"[{fitbit_user.fitbit_user_id}] {date} 실패 - "
                        f"Error: {result.get('error', 'Unknown')}"
                    )

        except Exception as e:
            log_message(f"[{fitbit_user.fitbit_user_id}] 예외 발생: {e}")

    log_message("\n=== 데이터 Backfill 완료 ===")


if __name__ == '__main__':
    # 목요일(10/31) ~ 금요일(11/1) 백필
    backfill_date_range('2025-10-31', '2025-11-01')
