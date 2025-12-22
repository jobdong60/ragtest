# Fitbit 데이터 자동 동기화 설정

## 개요
모든 Fitbit 사용자의 데이터를 5분마다 자동으로 동기화합니다.

## 파일 구조
```
myhealth-app/
├── sync_all_users.py       # 메인 동기화 스크립트
├── setup_cron.sh            # cron job 설정 스크립트
├── logs/
│   └── sync.log            # 동기화 로그 (자동 생성)
└── fitbit/
    ├── fitbit_api.py       # Fitbit API 호출 함수
    ├── data_sync.py        # DB 저장 함수
    └── token_refresh.py    # 토큰 갱신 함수
```

## Cron Job 설정

### 현재 설정
- **실행 주기**: 5분마다 (`*/5 * * * *`)
- **스크립트**: `/home/sehnr_kdca1885/myhealth-app/sync_all_users.py`
- **로그 파일**: `/home/sehnr_kdca1885/myhealth-app/logs/sync.log`

### Cron Job 확인
```bash
crontab -l
```

### Cron Job 삭제
```bash
crontab -e
# sync_all_users.py 라인 삭제 후 저장
```

### 수동 실행 (테스트용)
```bash
cd /home/sehnr_kdca1885/myhealth-app
./venv/bin/python sync_all_users.py
```

## 동작 과정

1. **모든 FitbitUser 조회**
   - DB에서 등록된 모든 사용자 가져오기

2. **각 사용자별로:**
   - Access Token 자동 갱신 (만료 방지)
   - 오늘 날짜의 데이터 가져오기:
     - 일일 요약 (걸음 수, 거리, 칼로리, 안정시 심박수 등)
     - 1분 단위 심박수 (IntradayHeartRate)
     - 5분 단위 걸음 수 (IntradaySteps)
     - 5분 단위 칼로리 (IntradayCalories)

3. **DB 저장**
   - 중복 방지: `update_or_create` 사용
   - 같은 날짜/시간 데이터는 업데이트

4. **로그 출력**
   - 성공/실패 개수
   - 저장된 레코드 수
   - 에러 메시지

## 로그 확인

### 실시간 로그 보기
```bash
tail -f /home/sehnr_kdca1885/myhealth-app/logs/sync.log
```

### 최근 로그 확인
```bash
tail -100 /home/sehnr_kdca1885/myhealth-app/logs/sync.log
```

### 로그 검색
```bash
# 특정 사용자 로그만 보기
grep "CRBM3W" /home/sehnr_kdca1885/myhealth-app/logs/sync.log

# 에러만 보기
grep -i "실패\|error\|fail" /home/sehnr_kdca1885/myhealth-app/logs/sync.log

# 오늘 날짜 로그만 보기
grep "2025-10-24" /home/sehnr_kdca1885/myhealth-app/logs/sync.log
```

## 주의사항

1. **토큰 갱신**:
   - Refresh token이 유효해야 자동 갱신 가능
   - 토큰이 완전히 만료되면 사용자가 재로그인 필요

2. **API Rate Limit**:
   - Fitbit API는 시간당 150회 제한
   - 5분마다 실행 시 사용자당 12회/시간
   - 최대 12명까지 안전

3. **로그 파일 관리**:
   - 로그가 계속 쌓이므로 주기적 정리 필요
   - logrotate 설정 권장

## 문제 해결

### Cron이 실행되지 않는 경우
```bash
# cron 서비스 상태 확인
sudo systemctl status cron

# cron 재시작
sudo systemctl restart cron
```

### 스크립트 권한 문제
```bash
chmod +x /home/sehnr_kdca1885/myhealth-app/sync_all_users.py
```

### Python 경로 문제
```bash
# venv의 Python 경로 확인
which python
/home/sehnr_kdca1885/myhealth-app/venv/bin/python --version
```

## 실행 주기 변경

### 1분마다 실행
```bash
crontab -e
# */1 * * * * ... 로 변경
```

### 10분마다 실행
```bash
crontab -e
# */10 * * * * ... 로 변경
```

### 매시간 정각 실행
```bash
crontab -e
# 0 * * * * ... 로 변경
```
