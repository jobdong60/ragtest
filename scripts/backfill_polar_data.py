#!/usr/bin/env python
"""
Polar 데이터 백필 스크립트
과거 데이터에 대해 이상치 제거 및 HRV 지표를 계산합니다.
"""

import os
import sys
import django
from datetime import datetime, timedelta
import pytz

# Django 환경 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhealth.settings')
django.setup()

from fitbit.models import PolarHeartRate
from django.db.models import Min, Max

def backfill_polar_data():
    """과거 데이터를 5분 단위로 처리"""
    print("=" * 80)
    print("Polar 데이터 백필 시작")
    print("=" * 80)
    
    # 데이터 범위 조회
    result = PolarHeartRate.objects.aggregate(Min('datetime'), Max('datetime'))
    start_datetime = result['datetime__min']
    end_datetime = result['datetime__max']
    
    if not start_datetime or not end_datetime:
        print("처리할 데이터가 없습니다.")
        return
    
    # UTC 시간대로 변환
    if start_datetime.tzinfo is None:
        start_datetime = pytz.UTC.localize(start_datetime)
    if end_datetime.tzinfo is None:
        end_datetime = pytz.UTC.localize(end_datetime)
    
    # 5분 단위로 내림
    start_datetime = start_datetime.replace(second=0, microsecond=0)
    start_datetime = start_datetime.replace(minute=(start_datetime.minute // 5) * 5)
    
    # 5분 단위로 올림
    end_datetime = end_datetime.replace(second=0, microsecond=0)
    if end_datetime.minute % 5 != 0:
        end_datetime = end_datetime.replace(minute=((end_datetime.minute // 5) + 1) * 5)
    
    print(f"\n데이터 범위: {start_datetime} ~ {end_datetime}")
    
    # 총 구간 수 계산
    total_intervals = int((end_datetime - start_datetime).total_seconds() / 300)  # 5분 = 300초
    print(f"총 처리할 5분 구간: {total_intervals}개")
    
    # 스크립트 경로
    outlier_script = os.path.join(os.path.dirname(__file__), 'remove_polar_outliers.py')
    hrv_script = os.path.join(os.path.dirname(__file__), 'calculate_polar_hrv_index.py')
    
    # 5분 단위로 반복
    current_time = start_datetime
    processed_count = 0
    error_count = 0
    
    print("\n" + "=" * 80)
    print("처리 시작")
    print("=" * 80 + "\n")
    
    while current_time < end_datetime:
        next_time = current_time + timedelta(minutes=5)
        processed_count += 1
        
        print(f"\n[{processed_count}/{total_intervals}] 처리 중: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 임시로 환경 변수에 시간 설정
        os.environ['BACKFILL_START_TIME'] = current_time.isoformat()
        os.environ['BACKFILL_END_TIME'] = next_time.isoformat()
        os.environ['BACKFILL_MODE'] = '1'
        
        # 1. 이상치 제거 스크립트 실행
        try:
            exec(open(outlier_script).read())
        except Exception as e:
            print(f"  ⚠️  이상치 제거 실패: {e}")
            error_count += 1
        
        # 2. HRV 지표 계산 스크립트 실행
        try:
            exec(open(hrv_script).read())
        except Exception as e:
            print(f"  ⚠️  HRV 계산 실패: {e}")
            error_count += 1
        
        current_time = next_time
    
    # 환경 변수 정리
    if 'BACKFILL_START_TIME' in os.environ:
        del os.environ['BACKFILL_START_TIME']
    if 'BACKFILL_END_TIME' in os.environ:
        del os.environ['BACKFILL_END_TIME']
    if 'BACKFILL_MODE' in os.environ:
        del os.environ['BACKFILL_MODE']
    
    print("\n" + "=" * 80)
    print("백필 완료")
    print("=" * 80)
    print(f"총 처리: {processed_count}개 구간")
    print(f"오류: {error_count}개")
    print("=" * 80)

if __name__ == "__main__":
    backfill_polar_data()

