#!/usr/bin/env python
"""
Polar HRV Index 백필 스크립트
과거 NN 데이터에 대해 HRV 지표를 계산하여 polar_heart_rate_index_5에 저장
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

from fitbit.models import PolarHeartRateNN, PolarHeartRateIndex5
from django.db.models import Min, Max
import numpy as np
from scipy import signal


def calculate_rmssd(rr_intervals):
    """RMSSD 계산: 연속된 RR 간격 차이의 제곱 평균의 제곱근"""
    if len(rr_intervals) < 2:
        return None
    
    diff_rr = np.diff(rr_intervals)
    rmssd = np.sqrt(np.mean(diff_rr**2))
    return float(rmssd)


def calculate_sdnn(rr_intervals):
    """SDNN 계산: RR 간격의 표준편차"""
    if len(rr_intervals) < 2:
        return None
    
    sdnn = np.std(rr_intervals, ddof=1)
    return float(sdnn)


def calculate_frequency_domain(rr_intervals, sampling_rate=4.0):
    """
    주파수 도메인 분석: HF, LF power 계산
    """
    if len(rr_intervals) < 10:
        return None, None, None
    
    try:
        # Welch's method로 PSD 계산
        freqs, psd = signal.welch(rr_intervals, fs=sampling_rate, nperseg=min(len(rr_intervals), 256))
        
        # HF (High Frequency): 0.15 - 0.4 Hz
        hf_mask = (freqs >= 0.15) & (freqs <= 0.4)
        hf_power = np.trapz(psd[hf_mask], freqs[hf_mask])
        
        # LF (Low Frequency): 0.04 - 0.15 Hz
        lf_mask = (freqs >= 0.04) & (freqs < 0.15)
        lf_power = np.trapz(psd[lf_mask], freqs[lf_mask])
        
        # LF/HF ratio
        lf_hf_ratio = lf_power / hf_power if hf_power > 0 else None
        
        return float(hf_power), float(lf_power), float(lf_hf_ratio) if lf_hf_ratio else None
    
    except Exception:
        return None, None, None


def process_interval(start_time, end_time):
    """
    특정 시간 구간의 NN 데이터로 HRV 지표를 계산하고 저장
    """
    # 해당 구간의 고유 사용자 목록
    users = PolarHeartRateNN.objects.filter(
        datetime__gte=start_time,
        datetime__lt=end_time
    ).values('username', 'date_of_birth').distinct()
    
    if not users:
        return 0
    
    # 이미 처리된 사용자 목록
    already_processed = set(
        PolarHeartRateIndex5.objects.filter(
            datetime_start=start_time
        ).values_list('username', 'date_of_birth')
    )
    
    total_saved = 0
    
    for user in users:
        username = user['username']
        date_of_birth = user['date_of_birth']
        
        if not username or not date_of_birth:
            continue
        
        # 이미 처리된 사용자 스킵
        if (username, date_of_birth) in already_processed:
            continue
        
        # NN 데이터 조회
        nn_data = PolarHeartRateNN.objects.filter(
            username=username,
            date_of_birth=date_of_birth,
            datetime__gte=start_time,
            datetime__lt=end_time
        ).order_by('datetime')
        
        if not nn_data:
            continue
        
        nn_list = list(nn_data)
        
        if len(nn_list) < 2:
            continue
        
        # HR 값 추출
        hr_values = [d.hr for d in nn_list if d.hr is not None]
        
        # RR 값 추출
        rr_values = [d.rr for d in nn_list if d.rr is not None]
        
        # HR 통계
        mean_hr = np.mean(hr_values) if hr_values else None
        sd_hr = np.std(hr_values, ddof=1) if len(hr_values) > 1 else None
        hr_upper = mean_hr + 1.96 * sd_hr if mean_hr and sd_hr else None
        hr_lower = mean_hr - 1.96 * sd_hr if mean_hr and sd_hr else None
        
        # RR 통계
        mean_rr = np.mean(rr_values) if rr_values else None
        
        # HRV 지표
        rmssd = None
        sdnn = None
        hf_power = None
        lf_power = None
        lf_hf_ratio = None
        
        if len(rr_values) >= 2:
            rr_array = np.array(rr_values)
            
            # 시간 도메인
            rmssd = calculate_rmssd(rr_array)
            sdnn = calculate_sdnn(rr_array)
            
            # 주파수 도메인
            hf_power, lf_power, lf_hf_ratio = calculate_frequency_domain(rr_array)
        
        # 결과 저장
        try:
            PolarHeartRateIndex5.objects.create(
                username=username,
                date_of_birth=date_of_birth,
                datetime_start=start_time,
                datetime_end=end_time,
                rmssd=round(rmssd, 2) if rmssd else None,
                sdnn=round(sdnn, 2) if sdnn else None,
                hf_power=round(hf_power, 2) if hf_power else None,
                lf_power=round(lf_power, 2) if lf_power else None,
                lf_hf_ratio=round(lf_hf_ratio, 2) if lf_hf_ratio else None,
                mean_hr=round(mean_hr, 2) if mean_hr else None,
                sd_hr=round(sd_hr, 2) if sd_hr else None,
                hr_upper=round(hr_upper, 2) if hr_upper else None,
                hr_lower=round(hr_lower, 2) if hr_lower else None,
                mean_rr=round(mean_rr, 2) if mean_rr else None,
                data_count=len(nn_list)
            )
            total_saved += 1
        except Exception as e:
            print(f"  ⚠️  {username} ({date_of_birth}): 저장 실패 - {e}")
    
    return total_saved


def backfill_hrv():
    """과거 NN 데이터를 5분 단위로 처리하여 HRV 지표 계산"""
    print("=" * 80)
    print("Polar HRV 백필 시작")
    print("=" * 80)
    
    # 데이터 범위 조회
    result = PolarHeartRateNN.objects.aggregate(Min('datetime'), Max('datetime'))
    start_datetime = result['datetime__min']
    end_datetime = result['datetime__max']
    
    if not start_datetime or not end_datetime:
        print("처리할 NN 데이터가 없습니다.")
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
    backfill_hrv()

