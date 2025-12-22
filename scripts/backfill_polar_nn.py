#!/usr/bin/env python
"""
Polar Heart Rate NN 백필 스크립트
과거 데이터에 대해 이상치를 제거하고 polar_heart_rate_nn에 저장
"""
import os
import sys
import django
from datetime import datetime, timedelta
import pytz

# Django 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhealth.settings')
django.setup()

from fitbit.models import PolarHeartRate, PolarHeartRateNN
from django.db.models import Min, Max
import numpy as np


def process_interval(start_time, end_time):
    """
    특정 시간 구간의 데이터에서 이상치를 제거하고 저장
    """
    # 해당 구간의 고유 사용자 목록
    users = PolarHeartRate.objects.filter(
        datetime__gte=start_time,
        datetime__lt=end_time
    ).values('username', 'date_of_birth').distinct()
    
    if not users:
        return 0
    
    total_saved = 0
    
    for user in users:
        username = user['username']
        date_of_birth = user['date_of_birth']
        
        if not username or not date_of_birth:
            continue
        
        # 이미 처리된 데이터인지 확인
        if PolarHeartRateNN.objects.filter(
            username=username,
            date_of_birth=date_of_birth,
            datetime__gte=start_time,
            datetime__lt=end_time
        ).exists():
            continue
        
        # 원본 데이터 조회
        raw_data = PolarHeartRate.objects.filter(
            username=username,
            date_of_birth=date_of_birth,
            datetime__gte=start_time,
            datetime__lt=end_time
        ).order_by('datetime')
        
        if not raw_data:
            continue
        
        # HR, RR 값 추출 (0 값은 제외)
        hr_values = np.array([d.hr for d in raw_data if d.hr is not None and d.hr > 0])
        rr_values = np.array([d.rr for d in raw_data if d.rr is not None and d.rr > 0])
        
        # HR 이상치 제거 기준 계산
        if len(hr_values) > 1:
            hr_mean = np.mean(hr_values)
            hr_std = np.std(hr_values)
            hr_upper = hr_mean + 3 * hr_std
            hr_lower = hr_mean - 3 * hr_std
        else:
            hr_mean = hr_values[0] if len(hr_values) > 0 else 0
            hr_upper = float('inf')
            hr_lower = float('-inf')
        
        # RR 이상치 제거 기준 계산
        if len(rr_values) > 1:
            rr_mean = np.mean(rr_values)
            rr_std = np.std(rr_values)
            rr_upper = rr_mean + 3 * rr_std
            rr_lower = rr_mean - 3 * rr_std
        else:
            rr_mean = rr_values[0] if len(rr_values) > 0 else 0
            rr_upper = float('inf')
            rr_lower = float('-inf')
        
        # 이상치 제거 및 NN 데이터 생성
        nn_data_list = []
        outlier_count = 0

        for data_point in raw_data:
            processed_hr = data_point.hr if data_point.hr is not None and data_point.hr > 0 else None
            processed_rr = data_point.rr if data_point.rr is not None and data_point.rr > 0 else None
            is_outlier = False
            original_hr = None
            original_rr = None

            # HR 이상치 처리 (0이 아닌 경우만)
            if processed_hr is not None and not (hr_lower <= data_point.hr <= hr_upper):
                original_hr = data_point.hr
                processed_hr = int(round(hr_mean))
                is_outlier = True
                outlier_count += 1

            # RR 이상치 처리 (0이 아닌 경우만)
            if processed_rr is not None and not (rr_lower <= data_point.rr <= rr_upper):
                original_rr = data_point.rr
                processed_rr = int(round(rr_mean)) if rr_mean else None
                is_outlier = True
                outlier_count += 1

            nn_data_list.append(
                PolarHeartRateNN(
                    device_id=data_point.device_id,
                    datetime=data_point.datetime,
                    hr=processed_hr,
                    rr=processed_rr,
                    username=username,
                    date_of_birth=date_of_birth,
                    is_outlier_removed=is_outlier,
                    original_hr=original_hr,
                    original_rr=original_rr
                )
            )
        
        if nn_data_list:
            PolarHeartRateNN.objects.bulk_create(nn_data_list)
            total_saved += len(nn_data_list)
            if outlier_count > 0:
                print(f"  ✓ {username} ({date_of_birth}): {len(nn_data_list)}개 저장, {outlier_count}개 이상치 제거")
    
    return total_saved


def backfill_nn():
    """과거 데이터를 5분 단위로 처리하여 NN 테이블에 저장"""
    print("=" * 80)
    print("Polar NN 백필 시작")
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
    print(f"총 처리할 5분 구간: {total_intervals}개\n")
    
    # 5분 단위로 반복
    current_time = start_datetime
    processed_count = 0
    total_saved = 0
    
    while current_time < end_datetime:
        next_time = current_time + timedelta(minutes=5)
        processed_count += 1
        
        # 진행 상황 표시 (10개 구간마다)
        if processed_count % 10 == 0 or processed_count == 1:
            print(f"[{processed_count}/{total_intervals}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 해당 구간 처리
        saved = process_interval(current_time, next_time)
        total_saved += saved
        
        current_time = next_time
    
    print("\n" + "=" * 80)
    print("백필 완료")
    print("=" * 80)
    print(f"총 처리: {processed_count}개 구간")
    print(f"총 저장: {total_saved}개 레코드")
    print("=" * 80)


if __name__ == "__main__":
    backfill_nn()

