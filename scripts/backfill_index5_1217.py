#!/usr/bin/env python
"""
Polar HRV Index5 백필 스크립트 (2025-12-17 KST)
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


def backfill_hrv_indices_for_date(target_date_str):
    """
    특정 날짜의 HRV 지표를 5분 단위로 백필

    Args:
        target_date_str: 백필 날짜 (YYYY-MM-DD) - KST 기준
    """
    kst = pytz.timezone('Asia/Seoul')

    # KST 날짜의 시작과 끝 시각 계산
    date_start_kst = kst.localize(datetime.strptime(f"{target_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S"))
    date_end_kst = kst.localize(datetime.strptime(f"{target_date_str} 23:59:59", "%Y-%m-%d %H:%M:%S"))

    print(f"[백필 시작] {target_date_str} (KST)")
    print(f"처리 범위: {date_start_kst.strftime('%Y-%m-%d %H:%M:%S')} ~ {date_end_kst.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 기존 해당 날짜 데이터 삭제
    # KST 12/17 00:00:00 ~ 23:59:59는 UTC 12/16 15:00:00 ~ 12/17 14:59:59
    next_day_start_kst = date_start_kst + timedelta(days=1)
    deleted_count = PolarHeartRateIndex5.objects.filter(
        datetime_start__gte=date_start_kst,
        datetime_start__lt=next_day_start_kst
    ).delete()[0]
    print(f"기존 데이터 삭제: {deleted_count}개")

    # 2. 5분 단위로 구간 생성 (00:00:00부터 23:55:00까지)
    time_slots = []
    current_time = date_start_kst
    while current_time < date_end_kst:
        slot_end = current_time + timedelta(minutes=5)
        time_slots.append((current_time, slot_end))
        current_time = slot_end

    print(f"생성된 5분 구간 수: {len(time_slots)}개")

    # 3. 각 5분 구간마다 HRV 지표 계산
    total_processed = 0
    total_slots_with_data = 0

    for slot_start, slot_end in time_slots:
        # 해당 구간의 NN 데이터 조회
        nn_data = PolarHeartRateNN.objects.filter(
            datetime__gte=slot_start,
            datetime__lt=slot_end
        ).order_by('username', 'date_of_birth', 'datetime')

        if not nn_data.exists():
            continue

        total_slots_with_data += 1

        # 사용자별로 그룹화
        users = nn_data.values_list('username', 'date_of_birth').distinct()

        for username, date_of_birth in users:
            if not username or not date_of_birth:
                continue

            # 해당 사용자의 해당 구간 NN 데이터
            user_nn_data = nn_data.filter(
                username=username,
                date_of_birth=date_of_birth
            ).order_by('datetime')

            user_data_list = list(user_nn_data)

            if len(user_data_list) < 2:
                continue

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

            # polar_heart_rate_index_5에 저장 (update_or_create로 중복 방지)
            PolarHeartRateIndex5.objects.update_or_create(
                username=username,
                date_of_birth=date_of_birth,
                datetime_start=slot_start,
                defaults={
                    'datetime_end': slot_end,
                    'rmssd': rmssd,
                    'sdnn': sdnn,
                    'hf_power': hf_power,
                    'lf_power': lf_power,
                    'lf_hf_ratio': lf_hf_ratio,
                    'mean_hr': mean_hr,
                    'sd_hr': sd_hr,
                    'hr_upper': hr_upper,
                    'hr_lower': hr_lower,
                    'mean_rr': mean_rr,
                    'data_count': len(user_data_list)
                }
            )

            total_processed += 1

    print(f"\n[백필 완료]")
    print(f"  - 데이터가 있는 5분 구간: {total_slots_with_data}개")
    print(f"  - 생성된 index_5 레코드: {total_processed}개")


if __name__ == '__main__':
    try:
        # 2025-12-17 KST 백필
        backfill_hrv_indices_for_date('2025-12-17')
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
