# Polar Heart Rate 이상치 제거 자동화 설정

## 개요
5분마다 자동으로 실행되어 Polar 심박수 데이터의 이상치를 제거하고 `polar_heart_rate_nn` 테이블에 저장합니다.

## 이상치 제거 로직
- **기준**: 3 표준편차 (3σ)
- **방법**: 이전 5분간 데이터로 평균(mean)과 표준편차(std) 계산
- **처리**: 3σ 밖의 값을 해당 5분간 평균값으로 대체

## 설정 방법

### 1. 데이터베이스 마이그레이션

```bash
cd /home/sehnr_kdca1885/myhealth-app
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

### 2. 스크립트 실행 권한 부여

```bash
chmod +x /home/sehnr_kdca1885/myhealth-app/scripts/remove_polar_outliers.py
```

### 3. 수동 테스트

```bash
cd /home/sehnr_kdca1885/myhealth-app
source venv/bin/activate
python scripts/remove_polar_outliers.py
```

### 4. Cron Job 설정

```bash
crontab -e
```

다음 라인 추가 (5분마다 실행):

```cron
*/5 * * * * cd /home/sehnr_kdca1885/myhealth-app && /home/sehnr_kdca1885/myhealth-app/venv/bin/python /home/sehnr_kdca1885/myhealth-app/scripts/remove_polar_outliers.py >> /home/sehnr_kdca1885/myhealth-app/logs/polar_processing.log 2>&1
```

**실행 순서 (자동):**
1. `remove_polar_outliers.py` - 이상치 제거 → polar_heart_rate_nn
2. `calculate_polar_hrv_index.py` - HRV 지표 계산 → polar_heart_rate_index_5

### 5. 로그 디렉토리 생성 (필요시)

```bash
mkdir -p /home/sehnr_kdca1885/myhealth-app/logs
```

## 테이블 구조

### polar_heart_rate_nn
```
- device_id: 기기 MAC 주소
- datetime: 데이터 시각
- hr: 심박수 (이상치 제거됨)
- rr: RR 간격 (이상치 제거됨)
- username: 사용자명
- date_of_birth: 생년월일
- is_outlier_removed: 이상치가 제거되었는지 여부
- original_hr: 원본 HR (이상치인 경우)
- original_rr: 원본 RR (이상치인 경우)
- created_at: 생성 시각
```

## 모니터링

### 로그 확인
```bash
tail -f /home/sehnr_kdca1885/myhealth-app/logs/polar_outlier_removal.log
```

### Cron 실행 확인
```bash
crontab -l
```

### 최근 처리된 데이터 확인
```sql
SELECT COUNT(*), is_outlier_removed 
FROM polar_heart_rate_nn 
WHERE created_at > NOW() - INTERVAL '1 hour' 
GROUP BY is_outlier_removed;
```

## 주의사항

1. **중복 방지**: 이미 처리된 데이터는 다시 처리하지 않습니다
2. **표준편차 조건**: 데이터가 2개 이상일 때만 표준편차를 계산합니다
3. **사용자별 처리**: username + date_of_birth 조합별로 독립적으로 처리됩니다
4. **원본 보존**: 이상치로 판단된 경우 원본 값을 `original_hr`, `original_rr`에 저장합니다

