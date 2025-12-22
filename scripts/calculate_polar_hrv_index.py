#!/usr/bin/env python
"""
Polar HRV 지표 계산 스크립트
5분마다 polar_heart_rate_nn 데이터로부터 HRV 지표를 계산하여 polar_heart_rate_index_5에 저장
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
import numpy as np
from scipy import signal
from scipy.fft import fft


def calculate_rmssd(rr_intervals):
    """RMSSD 계산: 연속된 RR 간격 차이의 제곱근 평균"""
    if len(rr_intervals) < 2:
        return None
    
    diff = np.diff(rr_intervals)
    squared_diff = diff ** 2
    rmssd = np.sqrt(np.mean(squared_diff))
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
    
    Args:
        rr_intervals: RR 간격 배열 (ms)
        sampling_rate: 샘플링 레이트 (Hz), 기본값 4Hz
    
    Returns:
        (hf_power, lf_power, lf_hf_ratio)
    """
    if len(rr_intervals) < 10:  # 최소 데이터 요구사항
        return None, None, None
    
    try:
        # RR 간격을 등간격으로 리샘플링
        # 실제로는 불균등 간격이지만 간단한 선형 보간 사용
        rr_mean = np.mean(rr_intervals)
        
        # Welch's method로 PSD (Power Spectral Density) 계산
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
    
    except Exception as e:
        print(f"  주파수 도메인 분석 오류: {e}")
        return None, None, None


def calculate_hrv_indices():
    """
    최근 5분간의 polar_heart_rate_nn 데이터로 HRV 지표 계산
    """
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    five_minutes_ago = now - timedelta(minutes=5)
    
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] HRV 지표 계산 시작")
    print(f"처리 범위: {five_minutes_ago.strftime('%Y-%m-%d %H:%M:%S')} ~ {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 최근 5분간 NN 데이터 조회
    nn_data = PolarHeartRateNN.objects.filter(
        datetime__gte=five_minutes_ago,
        datetime__lt=now
    ).order_by('username', 'date_of_birth', 'datetime')
    
    if not nn_data.exists():
        print("처리할 NN 데이터가 없습니다.")
        return
    
    # 사용자별로 그룹화
    users = nn_data.values_list('username', 'date_of_birth').distinct()
    
    # 이미 처리된 사용자 목록 한 번에 조회 (N+1 쿼리 방지)
    already_processed = set(
        PolarHeartRateIndex5.objects.filter(
            datetime_start=five_minutes_ago
        ).values_list('username', 'date_of_birth')
    )
    
    total_processed = 0
    
    for username, date_of_birth in users:
        if not username or not date_of_birth:
            continue
        
        # 이미 처리된 구간인지 확인 (중복 방지)
        if (username, date_of_birth) in already_processed:
            print(f"  {username} ({date_of_birth}): 이미 처리됨, 스킵")
            continue
        
        # 해당 사용자의 최근 5분 NN 데이터
        user_nn_data = nn_data.filter(
            username=username,
            date_of_birth=date_of_birth
        ).order_by('datetime')
        
        user_data_list = list(user_nn_data)
        
        if len(user_data_list) < 2:
            print(f"  {username} ({date_of_birth}): 데이터 부족 ({len(user_data_list)}개), 스킵")
            continue
        
        print(f"\n처리 중: {username} ({date_of_birth}) - {len(user_data_list)}개 데이터")
        
        # HR 값 추출
        hr_values = [d.hr for d in user_data_list if d.hr is not None]
        
        # RR 값 추출 (NN 간격)
        rr_values = [d.rr for d in user_data_list if d.rr is not None]
        
        # HR 통계
        mean_hr = np.mean(hr_values) if hr_values else None
        sd_hr = np.std(hr_values, ddof=1) if len(hr_values) > 1 else None
        hr_upper = mean_hr + 1.96 * sd_hr if mean_hr and sd_hr else None
        hr_lower = mean_hr - 1.96 * sd_hr if mean_hr and sd_hr else None
        
        # RR 통계
        mean_rr = np.mean(rr_values) if rr_values else None
        
        # HRV 지표 (RR 간격 필요)
        rmssd = None
        sdnn = None
        hf_power = None
        lf_power = None
        lf_hf_ratio = None
        
        if len(rr_values) >= 2:
            rr_array = np.array(rr_values)
            
            # Time domain
            rmssd = calculate_rmssd(rr_array)
            sdnn = calculate_sdnn(rr_array)
            
            # Frequency domain (충분한 데이터가 있을 때만)
            if len(rr_values) >= 10:
                hf_power, lf_power, lf_hf_ratio = calculate_frequency_domain(rr_array)
        
        mean_hr_str = f"{mean_hr:.1f}" if mean_hr is not None else "N/A"
        sd_hr_str = f"{sd_hr:.1f}" if sd_hr is not None else "N/A"
        rmssd_str = f"{rmssd:.1f}" if rmssd is not None else "N/A"
        sdnn_str = f"{sdnn:.1f}" if sdnn is not None else "N/A"
        hf_str = f"{hf_power:.1f}" if hf_power is not None else "N/A"
        lf_str = f"{lf_power:.1f}" if lf_power is not None else "N/A"
        lf_hf_str = f"{lf_hf_ratio:.2f}" if lf_hf_ratio is not None else "N/A"
        
        print(f"  HR: mean={mean_hr_str}, sd={sd_hr_str}")
        print(f"  HRV: RMSSD={rmssd_str}, SDNN={sdnn_str}")
        print(f"  Freq: HF={hf_str}, LF={lf_str}, LF/HF={lf_hf_str}")
        
        # polar_heart_rate_index_5에 저장
        PolarHeartRateIndex5.objects.create(
            username=username,
            date_of_birth=date_of_birth,
            datetime_start=five_minutes_ago,
            datetime_end=now,
            rmssd=rmssd,
            sdnn=sdnn,
            hf_power=hf_power,
            lf_power=lf_power,
            lf_hf_ratio=lf_hf_ratio,
            mean_hr=mean_hr,
            sd_hr=sd_hr,
            hr_upper=hr_upper,
            hr_lower=hr_lower,
            mean_rr=mean_rr,
            data_count=len(user_data_list)
        )
        
        total_processed += 1
        print(f"  저장 완료")
    
    print(f"\n전체 처리 완료: {total_processed}명의 사용자")


if __name__ == '__main__':
    try:
        calculate_hrv_indices()
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

