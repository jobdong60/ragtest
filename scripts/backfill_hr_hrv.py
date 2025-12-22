#!/usr/bin/env python
"""
목금토(10/31, 11/1, 11/2) HR과 HRV 데이터만 가져오는 스크립트
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
from fitbit.models import FitbitUser, IntradayHeartRate, IntradayHRV
from fitbit.data_sync import save_intraday_heart_rate, save_intraday_hrv
from fitbit.fitbit_api import get_heart_rate_data, get_hrv_intraday_data
from fitbit.token_refresh import refresh_access_token


def log_message(message):
    """로그 메시지 출력 (시간 포함)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")


def backfill_hr_hrv(start_date, end_date):
    """
    특정 날짜 범위의 HR과 HRV 데이터만 가져옴

    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
    """
    log_message(f"=== HR/HRV 데이터 Backfill 시작: {start_date} ~ {end_date} ===")

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
    log_message("기존 HR/HRV 데이터 삭제 중...")
    import pytz
    kst = pytz.timezone('Asia/Seoul')

    for date in dates:
        # KST 날짜의 UTC 시작/종료 시간 계산
        # KST 2025-10-31 00:00:00 = UTC 2025-10-30 15:00:00
        # KST 2025-11-01 00:00:00 = UTC 2025-10-31 15:00:00

        date_start_kst = kst.localize(datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S"))
        date_end_kst = kst.localize(datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S"))

        date_start_utc = date_start_kst.astimezone(pytz.UTC)
        date_end_utc = date_end_kst.astimezone(pytz.UTC)

        hr_deleted = IntradayHeartRate.objects.filter(
            datetime__gte=date_start_utc,
            datetime__lte=date_end_utc
        ).delete()[0]

        hrv_deleted = IntradayHRV.objects.filter(
            datetime__gte=date_start_utc,
            datetime__lte=date_end_utc
        ).delete()[0]

        log_message(f"{date} 삭제: HR {hr_deleted}개, HRV {hrv_deleted}개")

    # 각 사용자별로 데이터 백필
    for fitbit_user in fitbit_users:
        log_message(f"\n[{fitbit_user.fitbit_user_id}] 백필 시작...")

        try:
            # 토큰 갱신
            if not refresh_access_token(fitbit_user):
                log_message(f"[{fitbit_user.fitbit_user_id}] 토큰 갱신 실패 - 스킵")
                continue

            # 각 날짜별로 HR/HRV 데이터 동기화
            for date in dates:
                log_message(f"[{fitbit_user.fitbit_user_id}] {date} 동기화 중...")

                # HR 데이터 가져오기
                heart_data = get_heart_rate_data(fitbit_user.access_token, date)
                hr_count = 0
                if heart_data:
                    hr_count = save_intraday_heart_rate(fitbit_user.fitbit_user_id, date, heart_data)

                # HRV 데이터 가져오기
                hrv_data = get_hrv_intraday_data(fitbit_user.access_token, date)
                hrv_count = 0
                if hrv_data:
                    hrv_count = save_intraday_hrv(fitbit_user.fitbit_user_id, date, hrv_data)

                log_message(
                    f"[{fitbit_user.fitbit_user_id}] {date} 완료 - HR: {hr_count}, HRV: {hrv_count}"
                )

        except Exception as e:
            log_message(f"[{fitbit_user.fitbit_user_id}] 예외 발생: {e}")

    log_message("\n=== HR/HRV 데이터 Backfill 완료 ===")


if __name__ == '__main__':
    # 목금토(10/31, 11/1, 11/2) 백필
    backfill_hr_hrv('2025-10-31', '2025-11-02')
