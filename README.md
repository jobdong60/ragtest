# MyHealth Partner - Fitbit Data Manager

Fitbit 데이터를 수집하고 관리하는 Django 웹 애플리케이션입니다.

## 기능

- Fitbit API 연동을 통한 건강 데이터 수집
- 일별 활동, 심박수, 칼로리 등 건강 지표 관리
- 관리자 및 사용자 대시보드
- 자동 데이터 동기화

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd myhealth-app
```

### 2. 가상환경 생성 및 활성화

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 실제 값으로 수정:

```bash
cp .env.example .env
```

`.env` 파일 내용:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=fitbit_data
DB_USER=fitbit_user
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432
GCP_PROJECT_ID=your-gcp-project-id
```

### 5. 데이터베이스 설정

PostgreSQL 데이터베이스를 생성하고 마이그레이션 실행:

```bash
python manage.py migrate
```

### 6. 서버 실행

```bash
python manage.py runserver
```

## 환경 변수

- `SECRET_KEY`: Django secret key
- `DEBUG`: 디버그 모드 (True/False)
- `DB_NAME`: 데이터베이스 이름
- `DB_USER`: 데이터베이스 사용자
- `DB_PASSWORD`: 데이터베이스 비밀번호
- `DB_HOST`: 데이터베이스 호스트
- `DB_PORT`: 데이터베이스 포트
- `GCP_PROJECT_ID`: GCP 프로젝트 ID

## 프로젝트 구조

```
myhealth-app/
├── manage.py              # Django 관리 스크립트
├── myhealth/              # 프로젝트 설정 폴더
├── fitbit/                # Fitbit 앱
├── templates/             # HTML 템플릿
├── scripts/               # 데이터 수집 및 동기화 스크립트
│   ├── collector.py
│   ├── sync_all_users.py
│   ├── update_zones.py
│   └── setup_cron.sh
├── migrations_scripts/    # 데이터 마이그레이션 스크립트
│   ├── migrate_to_local.py
│   └── copy_data.py
└── tests/                 # 테스트 파일
    └── test_intraday.py
```

## 보안 주의사항

⚠️ **절대 커밋하지 말아야 할 파일:**
- `.env` 파일
- 데이터베이스 백업 파일
- 로그 파일
- API 키가 포함된 설정 파일

## 라이선스

이 프로젝트는 개인 용도로 사용됩니다.
