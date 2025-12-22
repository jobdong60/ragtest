# Polar Heart Rate API 문서

## 개요
Polar 기기에서 실시간 심박수(HR)와 RR 간격 데이터를 수신하는 API입니다.

## API 엔드포인트

### 1. Polar 데이터 수신 (Data Upload)

**URL:** `POST /data/polar/heartrate/`

**인증:** API Key 필요 (Header: `X-API-Key` 또는 `Authorization: Bearer {API_KEY}`)

**Content-Type:** `application/json`

#### 요청 형식

##### 단일 데이터
```json
{
  "hr": 75,
  "rr": 800,
  "timestamp": 1678886400000,
  "deviceId": "24:AC:AC:0C:D8:6A",
  "username": "john",
  "dateofbirth": "1993-01-30"
}
```

##### 다중 데이터 (배열)
```json
[
  {
    "hr": 75,
    "rr": 800,
    "timestamp": 1678886400000,
    "deviceId": "24:AC:AC:0C:D8:6A",
    "username": "john",
    "dateofbirth": "1993-01-30"
  },
  {
    "hr": 76,
    "rr": 790,
    "timestamp": 1678886401000,
    "deviceId": "24:AC:AC:0C:D8:6A",
    "username": "john",
    "dateofbirth": "1993-01-30"
  }
]
```

#### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `hr` | integer | ✅ | 심박수 (bpm), 0-300 범위 |
| `rr` | integer | ❌ | RR 간격 (ms), 양수 |
| `timestamp` | integer | ✅ | Unix timestamp (밀리초) |
| `deviceId` | string | ✅ | Polar 기기 MAC 주소 (예: "24:AC:AC:0C:D8:6A") |
| `username` | string | ✅ | 사용자명 (polar_users 테이블의 username) |
| `dateofbirth` | string | ✅ | 생년월일 (YYYY-MM-DD 형식, 예: "1993-01-30") |

#### 응답 형식

##### 성공 (201 Created)
```json
{
  "status": "success",
  "message": "2 record(s) saved successfully",
  "saved_count": 2,
  "data": [
    {
      "id": 12345,
      "device_id": "24:AC:AC:0C:D8:6A",
      "datetime": "2025-12-11T03:20:00+00:00",
      "hr": 75,
      "rr": 800,
      "username": "john",
      "date_of_birth": "1993-01-30"
    }
  ]
}
```

##### 부분 성공 (일부 에러 포함)
```json
{
  "status": "success",
  "message": "1 record(s) saved successfully",
  "saved_count": 1,
  "data": [...],
  "errors": [
    "Item 1: Invalid heart rate value: 350"
  ],
  "error_count": 1
}
```

##### 실패 (400 Bad Request)
```json
{
  "status": "error",
  "message": "No data saved",
  "errors": [
    "Item 0: Missing required fields: username, dateofbirth"
  ]
}
```

##### 인증 실패 (401 Unauthorized)
```json
{
  "status": "error",
  "message": "Invalid or missing API key"
}
```

---

## cURL 예제

### 단일 데이터 전송
```bash
curl -X POST https://myhealthpartner.app/data/polar/heartrate/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "hr": 75,
    "rr": 800,
    "timestamp": 1733887200000,
    "deviceId": "24:AC:AC:0C:D8:6A",
    "username": "john",
    "dateofbirth": "1993-01-30"
  }'
```

### 다중 데이터 전송
```bash
curl -X POST https://myhealthpartner.app/data/polar/heartrate/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '[
    {
      "hr": 75,
      "rr": 800,
      "timestamp": 1733887200000,
      "deviceId": "24:AC:AC:0C:D8:6A",
      "username": "john",
      "dateofbirth": "1993-01-30"
    },
    {
      "hr": 76,
      "rr": 790,
      "timestamp": 1733887201000,
      "deviceId": "24:AC:AC:0C:D8:6A",
      "username": "john",
      "dateofbirth": "1993-01-30"
    }
  ]'
```

---

## 데이터 검증 규칙

1. **HR (심박수)**
   - 정수 또는 실수
   - 0 < hr ≤ 300
   - 범위 밖 값은 거부됨

2. **RR (RR 간격)**
   - 선택 사항
   - 양수여야 함
   - 0 이하 값은 거부됨

3. **Timestamp**
   - Unix timestamp (밀리초)
   - 유효한 날짜로 변환 가능해야 함

4. **DeviceId**
   - 문자열 형식
   - 일반적으로 MAC 주소 형식 (예: "24:AC:AC:0C:D8:6A")

5. **Username**
   - `polar_users` 테이블에 존재하는 username
   - 문자열, 최대 150자

6. **DateOfBirth**
   - YYYY-MM-DD 형식 필수 (예: "1993-01-30")
   - 유효한 날짜여야 함
   - `polar_users` 테이블의 date_of_birth와 매칭됨

---

## Python 예제

```python
import requests
import time

API_URL = "https://myhealthpartner.app/data/polar/heartrate/"
API_KEY = "YOUR_API_KEY_HERE"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# 단일 데이터
data = {
    "hr": 75,
    "rr": 800,
    "timestamp": int(time.time() * 1000),
    "deviceId": "24:AC:AC:0C:D8:6A",
    "username": "john",
    "dateofbirth": "1993-01-30"
}

response = requests.post(API_URL, json=data, headers=headers)
print(response.json())

# 다중 데이터
batch_data = [
    {
        "hr": 75,
        "rr": 800,
        "timestamp": int(time.time() * 1000),
        "deviceId": "24:AC:AC:0C:D8:6A",
        "username": "john",
        "dateofbirth": "1993-01-30"
    },
    {
        "hr": 76,
        "rr": 790,
        "timestamp": int(time.time() * 1000) + 1000,
        "deviceId": "24:AC:AC:0C:D8:6A",
        "username": "john",
        "dateofbirth": "1993-01-30"
    }
]

response = requests.post(API_URL, json=batch_data, headers=headers)
print(response.json())
```

---

## 데이터베이스 스키마

### polar_heart_rate 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | BIGINT | Primary Key (자동 생성) |
| `device_id` | VARCHAR(255) | Polar 기기 MAC 주소 |
| `username` | VARCHAR(150) | 사용자명 (polar_users.username FK) |
| `date_of_birth` | DATE | 사용자 생년월일 (polar_users.date_of_birth FK) |
| `datetime` | TIMESTAMP WITH TIME ZONE | 측정 시간 (UTC) |
| `hr` | INTEGER | 심박수 (bpm) |
| `rr` | INTEGER | RR 간격 (ms), NULL 가능 |
| `created_at` | TIMESTAMP WITH TIME ZONE | 레코드 생성 시간 |

### 인덱스
- `polar_heart_rate_user_dob_idx` ON (username, date_of_birth)
- `polar_heart_device__d61514_idx` ON (device_id, datetime DESC)
- `polar_heart_datetim_f8366f_idx` ON datetime DESC

---

## 주의사항

1. **API 키 보안**
   - API 키는 환경변수 `DATA_POLAR_ENDPOINT_API_KEY`에 설정
   - 절대 코드에 하드코딩하지 말 것

2. **Rate Limiting**
   - 현재 제한 없음 (추후 추가 예정)
   - 대량 데이터는 배열로 묶어서 전송 권장

3. **타임스탬프**
   - 반드시 밀리초 단위 Unix timestamp 사용
   - 서버는 UTC 기준으로 저장

4. **Username + DateOfBirth 검증**
   - username과 dateofbirth가 `polar_users` 테이블에 존재하지 않아도 데이터는 저장됨
   - 하지만 실시간 모니터링 페이지에서는 `polar_users` 테이블에 등록된 사용자만 조회 가능
   - username과 date_of_birth의 조합으로 사용자를 식별하여 데이터를 매칭함

---

## 로그

모든 요청/응답은 다음 로그에 기록됩니다:
- `/mnt/data/logs/polar.log`
- Django 로그 레벨: INFO

로그 형식:
```
[POLAR] Received POST request from 192.168.1.100
[POLAR] Request body: {"hr":75,"rr":800,...}
[POLAR] Processing array with 5 items
Polar data saved: Device=24:AC:AC:0C:D8:6A, User=john, DOB=1993-01-30, HR=75, RR=800, Time=2025-12-11 03:20:00
[POLAR] Saved 5 records, 0 errors
```

---

## 실시간 모니터링

데이터 전송 후 관리자 페이지에서 실시간 모니터링 가능:
- URL: `https://myhealthpartner.app/manager/subjects/`
- 사용자 이름으로 검색 → 실시간 HR/RR 차트 확인

---

## 문의

기술 지원: sehnr_kdca1885@myhealthpartner.app
