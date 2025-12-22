#!/usr/bin/env python
"""
목금토(10/31, 11/1, 11/2) 모든 intraday 데이터를 다시 가져오는 스크립트
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
from fitbit.models import (
    FitbitUser, IntradayHeartRate, IntradaySteps, IntradayCalories,
    IntradayDistance, IntradayFloors, IntradayElevation, IntradaySpO2, IntradayHRV
)
from fitbit.data_sync import sync_fitbit_data_for_date
from fitbit.token_refresh import refresh_access_token
import pytz


def log_message(message):
    """로그 메시지 출력 (시간 포함)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")


def backfill_all_intraday(start_date, end_date):
    """
    특정 날짜 범위의 모든 intraday 데이터를 다시 가져옴

    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
    """
    log_message(f"=== 모든 Intraday 데이터 Backfill 시작: {start_date} ~ {end_date} ===")

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

    # 기존 데이터 삭제
    log_message("기존 Intraday 데이터 삭제 중...")
    kst = pytz.timezone('Asia/Seoul')

    for date in dates:
        # KST 날짜의 UTC 시작/종료 시간 계산
        date_start_kst = kst.localize(datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S"))
        date_end_kst = kst.localize(datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S"))

        date_start_utc = date_start_kst.astimezone(pytz.UTC)
        date_end_utc = date_end_kst.astimezone(pytz.UTC)

        hr_deleted = IntradayHeartRate.objects.filter(
            datetime__gte=date_start_utc, datetime__lte=date_end_utc
        ).delete()[0]

        steps_deleted = IntradaySteps.objects.filter(
            datetime__gte=date_start_utc, datetime__lte=date_end_utc
        ).delete()[0]

        calories_deleted = IntradayCalories.objects.filter(
            datetime__gte=date_start_utc, datetime__lte=date_end_utc
        ).delete()[0]

        distance_deleted = IntradayDistance.objects.filter(
            datetime__gte=date_start_utc, datetime__lte=date_end_utc
        ).delete()[0]

        floors_deleted = IntradayFloors.objects.filter(
            datetime__gte=date_start_utc, datetime__lte=date_end_utc
        ).delete()[0]

        elevation_deleted = IntradayElevation.objects.filter(
            datetime__gte=date_start_utc, datetime__lte=date_end_utc
        ).delete()[0]

        spo2_deleted = IntradaySpO2.objects.filter(
            datetime__gte=date_start_utc, datetime__lte=date_end_utc
        ).delete()[0]

        hrv_deleted = IntradayHRV.objects.filter(
            datetime__gte=date_start_utc, datetime__lte=date_end_utc
        ).delete()[0]

        log_message(
            f"{date} 삭제: HR {hr_deleted}, Steps {steps_deleted}, Calories {calories_deleted}, "
            f"Distance {distance_deleted}, Floors {floors_deleted}, Elevation {elevation_deleted}, "
            f"SpO2 {spo2_deleted}, HRV {hrv_deleted}"
        )

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

    log_message("\n=== 모든 Intraday 데이터 Backfill 완료 ===")


if __name__ == '__main__':
    # 목금토(10/30, 10/31, 11/1) 백필
    backfill_all_intraday('2025-10-30', '2025-11-01')
