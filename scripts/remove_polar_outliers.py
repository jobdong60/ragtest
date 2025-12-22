#!/usr/bin/env python
"""
Polar Heart Rate 이상치 제거 스크립트
5분마다 실행되어 최근 5분간의 데이터에서 이상치를 제거하고 polar_heart_rate_nn에 저장
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
import numpy as np


def remove_outliers_and_save():
    """
    최근 5분간의 데이터에서 이상치를 제거하고 저장
    """
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    five_minutes_ago = now - timedelta(minutes=5)
    
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 이상치 제거 시작")
    print(f"처리 범위: {five_minutes_ago.strftime('%Y-%m-%d %H:%M:%S')} ~ {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 최근 5분간 데이터 조회 (이미 처리되지 않은 데이터만)
    recent_data = PolarHeartRate.objects.filter(
        datetime__gte=five_minutes_ago,
        datetime__lt=now
    ).order_by('username', 'date_of_birth', 'datetime')
    
    if not recent_data.exists():
        print("처리할 데이터가 없습니다.")
        return
    
    # 사용자별로 그룹화
    users = recent_data.values_list('username', 'date_of_birth').distinct()
    
    total_processed = 0
    total_outliers = 0
    
    for username, date_of_birth in users:
        if not username or not date_of_birth:
            continue
        
        # 해당 사용자의 최근 5분 데이터
        user_data = recent_data.filter(
            username=username,
            date_of_birth=date_of_birth
        )
        
        # 이미 처리된 데이터인지 확인 (중복 방지)
        processed_datetimes = set(
            PolarHeartRateNN.objects.filter(
                username=username,
                date_of_birth=date_of_birth,
                datetime__gte=five_minutes_ago,
                datetime__lt=now
            ).values_list('datetime', flat=True)
        )
        
        # 미처리 데이터만 필터링
        new_data = [d for d in user_data if d.datetime not in processed_datetimes]
        
        if not new_data:
            continue
        
        print(f"\n처리 중: {username} ({date_of_birth}) - {len(new_data)}개 데이터")
        
        # HR과 RR 값 추출 (0 값은 제외)
        hr_values = [d.hr for d in new_data if d.hr is not None and d.hr > 0]
        rr_values = [d.rr for d in new_data if d.rr is not None and d.rr > 0]
        
        # 통계 계산
        hr_mean = np.mean(hr_values) if hr_values else None
        hr_std = np.std(hr_values) if len(hr_values) > 1 else None
        rr_mean = np.mean(rr_values) if rr_values else None
        rr_std = np.std(rr_values) if len(rr_values) > 1 else None
        
        hr_mean_str = f"{hr_mean:.1f}" if hr_mean is not None else "N/A"
        hr_std_str = f"{hr_std:.1f}" if hr_std is not None else "N/A"
        rr_mean_str = f"{rr_mean:.1f}" if rr_mean is not None else "N/A"
        rr_std_str = f"{rr_std:.1f}" if rr_std is not None else "N/A"
        print(f"  HR: mean={hr_mean_str}, std={hr_std_str}")
        print(f"  RR: mean={rr_mean_str}, std={rr_std_str}")
        
        # 이상치 제거 및 저장
        outliers_count = 0
        for data in new_data:
            is_outlier = False
            new_hr = data.hr if data.hr > 0 else None
            new_rr = data.rr if data.rr is not None and data.rr > 0 else None
            original_hr = None
            original_rr = None

            # HR 이상치 체크 (3 표준편차) - 0이 아닌 경우만
            if new_hr is not None and hr_mean is not None and hr_std is not None and hr_std > 0:
                if abs(data.hr - hr_mean) > 3 * hr_std:
                    is_outlier = True
                    original_hr = data.hr
                    new_hr = int(round(hr_mean))
                    outliers_count += 1

            # RR 이상치 체크 (3 표준편차) - 0이 아닌 경우만
            if new_rr is not None and rr_mean is not None and rr_std is not None and rr_std > 0:
                if abs(data.rr - rr_mean) > 3 * rr_std:
                    is_outlier = True
                    original_rr = data.rr
                    new_rr = int(round(rr_mean))
                    outliers_count += 1

            # polar_heart_rate_nn에 저장
            PolarHeartRateNN.objects.create(
                device_id=data.device_id,
                datetime=data.datetime,
                hr=new_hr,
                rr=new_rr,
                username=data.username,
                date_of_birth=data.date_of_birth,
                is_outlier_removed=is_outlier,
                original_hr=original_hr,
                original_rr=original_rr
            )
        
        total_processed += len(new_data)
        total_outliers += outliers_count
        
        print(f"  처리 완료: {len(new_data)}개, 이상치 제거: {outliers_count}개")
    
    print(f"\n전체 처리 완료: {total_processed}개 데이터, {total_outliers}개 이상치 제거")


if __name__ == '__main__':
    try:
        remove_outliers_and_save()
        
        # 이상치 제거 완료 후, HRV 지표 계산 스크립트 실행
        print("\n" + "="*50)
        print("HRV 지표 계산 시작...")
        print("="*50 + "\n")
        
        import subprocess
        script_path = os.path.join(os.path.dirname(__file__), 'calculate_polar_hrv_index.py')
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True
        )
        
        # HRV 계산 결과 출력
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode != 0:
            print(f"HRV 계산 스크립트 실행 실패 (exit code: {result.returncode})")
            sys.exit(1)
        
        print("\n모든 처리 완료")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

