#!/usr/bin/env python
"""
날짜 범위로 한번에 intraday 데이터를 가져오는 백필 스크립트 (API 요청 최소화)
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
from fitbit.fitbit_api import (
    get_heart_rate_data, get_steps_intraday_data, get_calories_intraday_data,
    get_distance_intraday_data, get_floors_intraday_data, get_elevation_intraday_data,
    get_spo2_intraday_data, get_hrv_intraday_data
)
from fitbit.data_sync import (
    save_intraday_heart_rate, save_intraday_steps, save_intraday_calories,
    save_intraday_distance, save_intraday_floors, save_intraday_elevation,
    save_intraday_spo2, save_intraday_hrv
)
from fitbit.token_refresh import refresh_access_token
import pytz


def log_message(message):
    """로그 메시지 출력 (시간 포함)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")


def backfill_daterange(start_date, end_date):
    """
    날짜 범위로 한번에 intraday 데이터를 가져옴 (API 요청 최소화)

    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
    """
    log_message(f"=== 날짜 범위 Backfill 시작: {start_date} ~ {end_date} ===")

    # 모든 FitbitUser 가져오기
    fitbit_users = FitbitUser.objects.all()
    total_users = fitbit_users.count()

    if total_users == 0:
        log_message("백필할 사용자가 없습니다.")
        return

    log_message(f"총 {total_users}명의 사용자 데이터 백필 시작")

    # 기존 데이터 삭제
    log_message("기존 Intraday 데이터 삭제 중...")
    kst = pytz.timezone('Asia/Seoul')

    # 날짜 범위의 KST -> UTC 변환
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')

    date_start_kst = kst.localize(datetime.strptime(f"{start_date} 00:00:00", "%Y-%m-%d %H:%M:%S"))
    date_end_kst = kst.localize(datetime.strptime(f"{end_date} 23:59:59", "%Y-%m-%d %H:%M:%S"))

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
        f"삭제 완료: HR {hr_deleted}, Steps {steps_deleted}, Calories {calories_deleted}, "
        f"Distance {distance_deleted}, Floors {floors_deleted}, Elevation {elevation_deleted}, "
        f"SpO2 {spo2_deleted}, HRV {hrv_deleted}"
    )

    # 각 사용자별로 날짜 범위 데이터 한번에 가져오기
    for fitbit_user in fitbit_users:
        log_message(f"\n[{fitbit_user.fitbit_user_id}] 백필 시작...")

        try:
            # 토큰 갱신
            if not refresh_access_token(fitbit_user):
                log_message(f"[{fitbit_user.fitbit_user_id}] 토큰 갱신 실패 - 스킵")
                continue

            # 날짜 범위로 한번에 API 요청 (9개 API 요청만 사용)
            log_message(f"[{fitbit_user.fitbit_user_id}] {start_date} ~ {end_date} 동기화 중...")

            # HR 데이터 가져오기
            heart_data = get_heart_rate_data(
                fitbit_user.access_token, start_date, end_date=end_date
            )

            # Steps 데이터 가져오기
            steps_data = get_steps_intraday_data(
                fitbit_user.access_token, start_date, end_date=end_date
            )

            # Calories 데이터 가져오기
            calories_data = get_calories_intraday_data(
                fitbit_user.access_token, start_date, end_date=end_date
            )

            # Distance 데이터 가져오기
            distance_data = get_distance_intraday_data(
                fitbit_user.access_token, start_date, end_date=end_date
            )

            # Floors 데이터 가져오기
            floors_data = get_floors_intraday_data(
                fitbit_user.access_token, start_date, end_date=end_date
            )

            # Elevation 데이터 가져오기
            elevation_data = get_elevation_intraday_data(
                fitbit_user.access_token, start_date, end_date=end_date
            )

            # SpO2 데이터 가져오기
            spo2_data = get_spo2_intraday_data(
                fitbit_user.access_token, start_date
            )

            # HRV 데이터 가져오기
            hrv_data = get_hrv_intraday_data(
                fitbit_user.access_token, start_date
            )

            # 데이터 저장 (날짜별로 분리해서 저장)
            current_dt = start_dt
            hr_count = 0
            steps_count = 0
            calories_count = 0
            distance_count = 0
            floors_count = 0
            elevation_count = 0
            spo2_count = 0
            hrv_count = 0

            while current_dt <= end_dt:
                date_str = current_dt.strftime('%Y-%m-%d')

                # 각 데이터 타입별로 저장
                if heart_data:
                    hr_count += save_intraday_heart_rate(
                        fitbit_user.fitbit_user_id, date_str, heart_data
                    )

                if steps_data:
                    steps_count += save_intraday_steps(
                        fitbit_user.fitbit_user_id, date_str, steps_data
                    )

                if calories_data:
                    calories_count += save_intraday_calories(
                        fitbit_user.fitbit_user_id, date_str, calories_data
                    )

                if distance_data:
                    distance_count += save_intraday_distance(
                        fitbit_user.fitbit_user_id, date_str, distance_data
                    )

                if floors_data:
                    floors_count += save_intraday_floors(
                        fitbit_user.fitbit_user_id, date_str, floors_data
                    )

                if elevation_data:
                    elevation_count += save_intraday_elevation(
                        fitbit_user.fitbit_user_id, date_str, elevation_data
                    )

                if spo2_data:
                    spo2_count += save_intraday_spo2(
                        fitbit_user.fitbit_user_id, date_str, spo2_data
                    )

                if hrv_data:
                    hrv_count += save_intraday_hrv(
                        fitbit_user.fitbit_user_id, date_str, hrv_data
                    )

                current_dt += timedelta(days=1)

            log_message(
                f"[{fitbit_user.fitbit_user_id}] 완료 - "
                f"HR: {hr_count}, Steps: {steps_count}, Calories: {calories_count}, "
                f"Distance: {distance_count}, Floors: {floors_count}, Elevation: {elevation_count}, "
                f"SpO2: {spo2_count}, HRV: {hrv_count}"
            )

        except Exception as e:
            log_message(f"[{fitbit_user.fitbit_user_id}] 예외 발생: {e}")
            import traceback
            traceback.print_exc()

    log_message("\n=== 날짜 범위 Backfill 완료 ===")


if __name__ == '__main__':
    # 목금토(10/30, 10/31, 11/1) 백필
    backfill_daterange('2025-10-30', '2025-11-01')
