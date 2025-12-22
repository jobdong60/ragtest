#!/usr/bin/env python
"""
수면 관련 데이터 수집 테스트 스크립트
KST 기준 오늘(2025-11-27) 데이터를 가져와서 테스트
"""
import os
import sys
import django
from datetime import datetime

# Django 환경 설정
sys.path.append('/home/sehnr_kdca1885/myhealth-app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhealth.settings')
django.setup()

# Django 모델 및 함수 import
from fitbit.models import FitbitUser
from fitbit.fitbit_api import (
    get_sleep_data,
    get_breathing_rate_data,
    get_skin_temperature_data
)
from fitbit.data_sync import (
    save_sleep_log,
    save_breathing_rate,
    save_skin_temperature
)
from fitbit.token_refresh import refresh_access_token


def log_message(message):
    """로그 메시지 출력 (시간 포함)"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")


def test_sleep_data_collection():
    """CRBM3W 유저의 오늘 수면 데이터 수집 테스트"""

    # 테스트할 유저 ID와 날짜
    test_user_id = 'CRBM3W'
    test_date = '2025-11-28'  # KST 오늘 (수면 데이터 확인용)

    log_message(f"=== 수면 데이터 수집 테스트 시작 ({test_user_id}, {test_date}) ===")

    try:
        # FitbitUser 가져오기
        fitbit_user = FitbitUser.objects.get(fitbit_user_id=test_user_id)
        log_message(f"유저 찾음: {fitbit_user.fitbit_user_id}")

        # 토큰 갱신
        log_message("액세스 토큰 갱신 중...")
        if not refresh_access_token(fitbit_user):
            log_message("❌ 토큰 갱신 실패")
            return False

        log_message("✅ 토큰 갱신 성공")
        access_token = fitbit_user.access_token

        # 1. 수면 데이터 수집
        log_message("\n--- 1. 수면 데이터 수집 ---")
        sleep_data = get_sleep_data(access_token, test_date)
        if sleep_data:
            log_message(f"수면 API 응답: {sleep_data.keys()}")
            if 'sleep' in sleep_data:
                log_message(f"수면 로그 개수: {len(sleep_data['sleep'])}개")
                for i, sleep in enumerate(sleep_data['sleep'], 1):
                    log_message(f"  수면 #{i}: {sleep.get('startTime')} ~ {sleep.get('endTime')}")
                    log_message(f"    분류: {'주요 수면' if sleep.get('isMainSleep') else '낮잠'}")
                    log_message(f"    총 수면: {sleep.get('minutesAsleep')}분")

            # DB 저장
            saved = save_sleep_log(test_user_id, test_date, sleep_data)
            log_message(f"✅ 수면 데이터 {saved}개 저장 완료")
        else:
            log_message("❌ 수면 데이터 없음")

        # 2. 호흡수 데이터 수집
        log_message("\n--- 2. 호흡수 데이터 수집 ---")
        br_data = get_breathing_rate_data(access_token, test_date)
        if br_data:
            log_message(f"호흡수 API 응답: {br_data.keys()}")
            if 'br' in br_data:
                log_message(f"호흡수 데이터 개수: {len(br_data['br'])}개")
                for item in br_data['br']:
                    br_value = item.get('value', {}).get('breathingRate')
                    log_message(f"  날짜: {item.get('dateTime')}, 호흡수: {br_value} breaths/min")

            # DB 저장
            saved = save_breathing_rate(test_user_id, test_date, br_data)
            log_message(f"✅ 호흡수 데이터 {saved}개 저장 완료")
        else:
            log_message("❌ 호흡수 데이터 없음")

        # 3. 피부 온도 데이터 수집
        log_message("\n--- 3. 피부 온도 데이터 수집 ---")
        temp_data = get_skin_temperature_data(access_token, test_date)
        if temp_data:
            log_message(f"피부 온도 API 응답: {temp_data.keys()}")
            if 'tempSkin' in temp_data:
                log_message(f"피부 온도 데이터 개수: {len(temp_data['tempSkin'])}개")
                for item in temp_data['tempSkin']:
                    temp_value = item.get('value', {}).get('nightlyRelative')
                    log_message(f"  날짜: {item.get('dateTime')}, 상대 온도: {temp_value}°C")

            # DB 저장
            saved = save_skin_temperature(test_user_id, test_date, temp_data)
            log_message(f"✅ 피부 온도 데이터 {saved}개 저장 완료")
        else:
            log_message("❌ 피부 온도 데이터 없음")

        log_message("\n=== 테스트 완료 ===")
        return True

    except FitbitUser.DoesNotExist:
        log_message(f"❌ 유저 {test_user_id}를 찾을 수 없습니다.")
        return False
    except Exception as e:
        log_message(f"❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_sleep_data_collection()
