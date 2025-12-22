#!/usr/bin/env python
"""
수면 API 응답 디버깅 스크립트
실제 API 응답을 출력해서 수면 단계 데이터 확인
"""
import os
import sys
import django
from datetime import datetime
import json

# Django 환경 설정
sys.path.append('/home/sehnr_kdca1885/myhealth-app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhealth.settings')
django.setup()

from fitbit.models import FitbitUser
from fitbit.fitbit_api import get_sleep_data
from fitbit.token_refresh import refresh_access_token


def debug_sleep_api():
    """수면 API 응답 디버깅"""
    test_user_id = 'CRBM3W'
    test_date = '2025-11-28'

    print(f"=== 수면 API 응답 디버깅 ({test_user_id}, {test_date}) ===\n")

    try:
        fitbit_user = FitbitUser.objects.get(fitbit_user_id=test_user_id)

        # 토큰 갱신
        if not refresh_access_token(fitbit_user):
            print("❌ 토큰 갱신 실패")
            return

        # 수면 데이터 가져오기
        sleep_data = get_sleep_data(fitbit_user.access_token, test_date)

        if not sleep_data:
            print("❌ 수면 데이터 없음")
            return

        # 전체 응답 출력
        print("전체 API 응답:")
        print(json.dumps(sleep_data, indent=2, ensure_ascii=False))
        print("\n" + "="*80 + "\n")

        # 수면 로그별 상세 정보
        if 'sleep' in sleep_data:
            for i, sleep in enumerate(sleep_data['sleep'], 1):
                print(f"수면 로그 #{i}:")
                print(f"  logId: {sleep.get('logId')}")
                print(f"  dateOfSleep: {sleep.get('dateOfSleep')}")
                print(f"  startTime: {sleep.get('startTime')}")
                print(f"  endTime: {sleep.get('endTime')}")
                print(f"  duration: {sleep.get('duration')} ms")
                print(f"  minutesAsleep: {sleep.get('minutesAsleep')}")
                print(f"  minutesAwake: {sleep.get('minutesAwake')}")
                print(f"  efficiency: {sleep.get('efficiency')}")
                print(f"  isMainSleep: {sleep.get('isMainSleep')}")

                # 수면 단계 정보
                levels = sleep.get('levels', {})
                print(f"\n  수면 단계 (levels):")
                print(f"    summary 키: {list(levels.get('summary', {}).keys())}")

                summary = levels.get('summary', {})
                for stage_name, stage_data in summary.items():
                    print(f"    {stage_name}: {stage_data}")

                print()

    except FitbitUser.DoesNotExist:
        print(f"❌ 유저 {test_user_id}를 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    debug_sleep_api()
