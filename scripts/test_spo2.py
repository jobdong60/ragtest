#!/usr/bin/env python
"""
SpO2 데이터 수집 테스트 (어제, 오늘 모두)
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Django 환경 설정
sys.path.append('/home/sehnr_kdca1885/myhealth-app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhealth.settings')
django.setup()

from fitbit.models import FitbitUser
from fitbit.fitbit_api import get_spo2_intraday_data
from fitbit.data_sync import save_intraday_spo2
from fitbit.token_refresh import refresh_access_token


def test_spo2():
    """SpO2 데이터 테스트"""
    test_user_id = 'CRBM3W'

    # 어제와 오늘 날짜
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    dates = [yesterday, today]

    print(f"=== SpO2 데이터 수집 테스트 ({test_user_id}) ===\n")

    try:
        fitbit_user = FitbitUser.objects.get(fitbit_user_id=test_user_id)

        # 토큰 갱신
        if not refresh_access_token(fitbit_user):
            print("❌ 토큰 갱신 실패")
            return

        print("✅ 토큰 갱신 성공\n")

        for date in dates:
            print(f"--- {date} SpO2 데이터 ---")

            # SpO2 intraday 데이터 가져오기
            spo2_data = get_spo2_intraday_data(fitbit_user.access_token, date)

            if spo2_data:
                # 전체 응답 출력
                import json
                print(f"API 응답 타입: {type(spo2_data)}")
                print(json.dumps(spo2_data, indent=2))

                # DB 저장
                saved = save_intraday_spo2(test_user_id, date, spo2_data)
                print(f"✅ SpO2 데이터 {saved}개 저장 완료\n")
            else:
                print(f"❌ {date} SpO2 데이터 없음\n")

    except FitbitUser.DoesNotExist:
        print(f"❌ 유저 {test_user_id}를 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_spo2()
