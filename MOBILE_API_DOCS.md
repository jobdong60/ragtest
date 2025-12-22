# MyHealth Partner - 모바일 앱 API 문서

## Base URL
```
https://myhealthpartner.app
```

## 인증 방식
JWT (JSON Web Token) 기반 인증을 사용합니다.

---

## 1. 회원가입

**Endpoint:** `POST /api/mobile/register/`

**인증 필요:** 없음

**Request Body:**
```json
{
  "username": "user123",      // 필수
  "password": "password123"   // 필수
}
```

**Response (성공):**
```json
{
  "success": true,
  "message": "회원가입이 완료되었습니다.",
  "user": {
    "id": 1,
    "username": "user123",
    "email": null,
    "full_name": null
  }
}
```

**Response (실패):**
```json
{
  "success": false,
  "message": "이미 존재하는 사용자명입니다."
}
```

**Status Codes:**
- `201`: 회원가입 성공
- `400`: 잘못된 요청 (필수 필드 누락, 중복 사용자명 등)
- `500`: 서버 오류

---

## 2. 로그인

**Endpoint:** `POST /api/mobile/login/`

**인증 필요:** 없음

**Request Body:**
```json
{
  "username": "user123",
  "password": "password123"
}
```

**Response (성공):**
```json
{
  "success": true,
  "message": "로그인에 성공했습니다.",
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "user": {
    "id": 1,
    "username": "user123",
    "email": "user@example.com",
    "full_name": "홍길동",
    "phone_number": "010-1234-5678",
    "gender": "MALE",
    "date_of_birth": "1990-01-01",
    "age": 35,
    "height": 175.5,
    "weight": 70.2,
    "polar_device_id": null
  }
}
```

**Response (실패):**
```json
{
  "success": false,
  "message": "사용자를 찾을 수 없습니다."
}
```

**Status Codes:**
- `200`: 로그인 성공
- `400`: 필수 필드 누락
- `401`: 비밀번호 오류
- `403`: 비활성화된 계정
- `404`: 사용자 없음
- `500`: 서버 오류

**토큰 저장:**
- `access` 토큰: 24시간 유효, API 요청 시 사용
- `refresh` 토큰: 30일 유효, access 토큰 갱신 시 사용

---

## 3. 토큰 갱신 (Refresh)

**Endpoint:** `POST /api/mobile/token/refresh/`

**인증 필요:** 없음

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (성공):**
```json
{
  "success": true,
  "message": "토큰이 갱신되었습니다.",
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

**Response (실패):**
```json
{
  "success": false,
  "message": "유효하지 않거나 만료된 refresh token입니다."
}
```

**Status Codes:**
- `200`: 갱신 성공
- `400`: refresh token 누락
- `401`: 유효하지 않거나 만료된 토큰
- `403`: 비활성화된 계정
- `404`: 사용자 없음
- `500`: 서버 오류

**참고:**
- Refresh token을 사용하면 새로운 access token과 refresh token을 모두 받습니다
- 기존 refresh token은 무효화되지 않습니다 (BLACKLIST_AFTER_ROTATION=False)
- 새로 받은 토큰들로 기존 토큰을 교체해야 합니다

---

## 4. 프로필 조회

**Endpoint:** `GET /api/mobile/profile/`

**인증 필요:** 예 (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (성공):**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "user123",
    "email": "user@example.com",
    "full_name": "홍길동",
    "phone_number": "010-1234-5678",
    "gender": "MALE",
    "date_of_birth": "1990-01-01",
    "age": 35,
    "height": 175.5,
    "weight": 70.2,
    "polar_device_id": null,
    "created_at": "2025-12-09T10:00:00+09:00",
    "last_login": "2025-12-09T15:30:00+09:00"
  }
}
```

**Status Codes:**
- `200`: 조회 성공
- `401`: 인증 실패 (토큰 없음 또는 만료)
- `404`: 사용자 없음
- `500`: 서버 오류

---

## 5. 프로필 수정

**Endpoint:** `PUT /api/mobile/profile/update/`

**인증 필요:** 예 (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (모든 필드 선택):**
```json
{
  "full_name": "김철수",
  "email": "new@example.com",
  "phone_number": "010-9999-8888",
  "gender": "MALE",
  "date_of_birth": "1990-01-01",
  "age": 36,
  "height": 176.0,
  "weight": 68.5
}
```

**참고:**
- 모든 필드는 선택사항입니다
- 수정하고 싶은 필드만 포함하면 됩니다
- `polar_device_id`는 사용자가 수정하지 않습니다 (시스템 관리)

**Response (성공):**
```json
{
  "success": true,
  "message": "프로필이 수정되었습니다.",
  "user": {
    "id": 1,
    "username": "user123",
    "email": "new@example.com",
    "full_name": "김철수",
    "phone_number": "010-9999-8888",
    "gender": "MALE",
    "date_of_birth": "1990-01-01",
    "age": 36,
    "height": 176.0,
    "weight": 68.5,
    "polar_device_id": null
  }
}
```

**Status Codes:**
- `200`: 수정 성공
- `400`: 잘못된 요청 (이메일 중복, 날짜 형식 오류 등)
- `401`: 인증 실패
- `404`: 사용자 없음
- `500`: 서버 오류

---

## 6. Polar 심박수 데이터 전송

**Endpoint:** `POST /data/polar/heartrate/`

**인증 필요:** 예 (API Key)

**Headers:**
```
X-API-Key: <API_KEY>
Content-Type: application/json
```

**Request Body (단일 데이터):**
```json
{
  "hr": 75,
  "rr": 800,
  "timestamp": 1702123456789,
  "deviceId": "24:AC:AC:0C:D8:6A"
}
```

**Request Body (배치 데이터):**
```json
[
  {
    "hr": 75,
    "rr": 800,
    "timestamp": 1702123456789,
    "deviceId": "24:AC:AC:0C:D8:6A"
  },
  {
    "hr": 76,
    "rr": 790,
    "timestamp": 1702123457789,
    "deviceId": "24:AC:AC:0C:D8:6A"
  }
]
```

**필드 설명:**
- `hr`: 심박수 (bpm, 필수, 0-300)
- `rr`: RR 간격 (ms, 선택)
- `timestamp`: Unix timestamp (밀리초, 필수)
- `deviceId`: Polar 기기 MAC 주소 (필수)

**Response (성공):**
```json
{
  "status": "success",
  "message": "2 record(s) saved successfully",
  "saved_count": 2,
  "data": [...]
}
```

**Status Codes:**
- `201`: 저장 성공
- `400`: 잘못된 요청 (필수 필드 누락, 잘못된 값 등)
- `401`: API Key 인증 실패
- `500`: 서버 오류

---

## 인증 처리 가이드

### 1. 로그인 후 토큰 저장
```javascript
// 로그인 응답에서 토큰 저장
const response = await login(username, password);
if (response.success) {
  // 로컬 스토리지 또는 보안 저장소에 저장
  saveToken('access_token', response.tokens.access);
  saveToken('refresh_token', response.tokens.refresh);
}
```

### 2. API 요청 시 토큰 사용
```javascript
// 프로필 조회 예시
const accessToken = getToken('access_token');
const response = await fetch('https://myhealthpartner.app/api/mobile/profile/', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
```

### 3. 401 에러 처리 (토큰 만료 시 자동 갱신)
```javascript
// API 요청 래퍼 함수
async function apiRequest(url, options = {}) {
  let accessToken = await getToken('access_token');

  // 첫 번째 시도
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  });

  // Access Token 만료 시
  if (response.status === 401) {
    // Refresh Token으로 갱신 시도
    const refreshToken = await getToken('refresh_token');

    const refreshResponse = await fetch('https://myhealthpartner.app/api/mobile/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken })
    });

    if (refreshResponse.ok) {
      const data = await refreshResponse.json();

      // 새 토큰 저장
      await saveToken('access_token', data.tokens.access);
      await saveToken('refresh_token', data.tokens.refresh);

      // 원래 요청 재시도
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${data.tokens.access}`,
          'Content-Type': 'application/json'
        }
      });
    } else {
      // Refresh Token도 만료됨 → 로그인 필요
      navigateToLogin();
      return null;
    }
  }

  return response;
}

// 사용 예시
const response = await apiRequest('https://myhealthpartner.app/api/mobile/profile/', {
  method: 'GET'
});
const data = await response.json();
```

---

## 데이터 타입

### Gender (성별)
- `"MALE"`: 남성
- `"FEMALE"`: 여성
- `"OTHER"`: 기타

### Date Format (날짜)
- 형식: `"YYYY-MM-DD"`
- 예시: `"1990-01-01"`

### Timestamp
- Unix timestamp (밀리초)
- 예시: `1702123456789`

---

## 에러 코드 정리

| Status Code | 의미 | 처리 방법 |
|------------|------|----------|
| 200 | 성공 | - |
| 201 | 생성 성공 | - |
| 400 | 잘못된 요청 | 에러 메시지 확인 후 수정 |
| 401 | 인증 실패 | 로그인 페이지로 이동 |
| 403 | 권한 없음 | 계정 상태 확인 |
| 404 | 리소스 없음 | 에러 메시지 표시 |
| 500 | 서버 오류 | 나중에 다시 시도 |

---

## 테스트 순서

1. **회원가입**
   ```bash
   curl -X POST https://myhealthpartner.app/api/mobile/register/ \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"test1234"}'
   ```

2. **로그인**
   ```bash
   curl -X POST https://myhealthpartner.app/api/mobile/login/ \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"test1234"}'
   ```

3. **프로필 조회** (토큰 사용)
   ```bash
   curl -X GET https://myhealthpartner.app/api/mobile/profile/ \
     -H "Authorization: Bearer <access_token>"
   ```

4. **프로필 수정** (토큰 사용)
   ```bash
   curl -X PUT https://myhealthpartner.app/api/mobile/profile/update/ \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"full_name":"홍길동","age":35,"height":175.5,"weight":70.2}'
   ```

---

## 문의사항
API 관련 문의사항이나 오류 발견 시 백엔드 개발팀에 연락 바랍니다.
