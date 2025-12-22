import os
import base64
import requests
import pg8000.dbapi
import sys
from datetime import datetime
from google.cloud import secretmanager
from google.cloud.sql.connector import Connector

# --- ★★★★★ 관리자 설정 영역 ★★★★★ ---
# 미국 심장 협회(AHA), CDC 가이드라인 기반 추천 값 (평균 40세 기준)
# 최대 심박수 (MHR) = 220 - 40 = 180 bpm
CUSTOM_HEART_RATE_ZONES = {
    # 지방 연소 구간 (MHR의 50% ~ 69%): 90 ~ 125 bpm
    "fatBurnZone": {"min": 90, "max": 125},
    # 심장 강화 구간 (MHR의 70% ~ 84%): 126 ~ 151 bpm
    "cardioZone": {"min": 126, "max": 151},
    # 최대 구간 (MHR의 85% 이상): 152 ~ 220 bpm (상한은 넉넉하게 설정)
    "peakZone": {"min": 152, "max": 220}
}
# --- 설정 끝 ---


# --- 설정 값 로드 ---
try:
    GCP_PROJECT_ID = "api-test-468900"
    
    if GCP_PROJECT_ID == "YOUR_GCP_PROJECT_ID_HERE" or not GCP_PROJECT_ID:
        print("FATAL ERROR: GCP_PROJECT_ID is not set.", file=sys.stderr)
        sys.exit(1)

    SECRET_CLIENT = secretmanager.SecretManagerServiceClient()

    def get_secret(secret_id, version_id="latest"):
        name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
        response = SECRET_CLIENT.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")

    DB_USER = get_secret("db-user")
    DB_PASS = get_secret("db-pass")
    DB_NAME = "fitbit_data"
    INSTANCE_CONNECTION_NAME = get_secret("db-connection-name")
    FITBIT_CLIENT_ID = get_secret("fitbit-client-id")
    FITBIT_CLIENT_SECRET = get_secret("fitbit-client-secret")

except Exception as e:
    print(f"FATAL ERROR during initialization: {e}", file=sys.stderr)
    sys.exit(1)

# --- Cloud SQL Connector 초기화 ---
connector = Connector()

def get_conn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

# --- Fitbit API 설정 ---
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_API_BASE_URL = "https://api.fitbit.com"

# --- 메인 로직 ---

def update_user_profile(user_id, access_token):
    """Fitbit API를 호출하여 사용자의 프로필(심박수 구간)을 업데이트합니다."""
    headers = {'Authorization': f'Bearer {access_token}'}
    profile_update_endpoint = f"{FITBIT_API_BASE_URL}/1/user/-/profile.json"
    
    # Fitbit API에 보낼 데이터. customHeartRateZones를 활성화하고 값을 전달합니다.
    data = {
        "useCustomHeartRateZones": "true",
        "fatBurnZoneMin": CUSTOM_HEART_RATE_ZONES["fatBurnZone"]["min"],
        "fatBurnZoneMax": CUSTOM_HEART_RATE_ZONES["fatBurnZone"]["max"],
        "cardioZoneMin": CUSTOM_HEART_RATE_ZONES["cardioZone"]["min"],
        "cardioZoneMax": CUSTOM_HEART_RATE_ZONES["cardioZone"]["max"],
        "peakZoneMin": CUSTOM_HEART_RATE_ZONES["peakZone"]["min"],
        "peakZoneMax": CUSTOM_HEART_RATE_ZONES["peakZone"]["max"],
    }
    
    try:
        response = requests.post(profile_update_endpoint, headers=headers, data=data)
        response.raise_for_status() # 오류가 있으면 예외 발생
        print(f"[SUCCESS] Successfully updated heart rate zones for user {user_id}.")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] Failed to update profile for user {user_id}: {e.response.text}")
        return False


def main():
    """메인 실행 함수"""
    print(f"--- Starting heart rate zone update job at {datetime.now()} ---")
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # DB에서 모든 사용자 정보 가져오기 (access_token이 필요합니다)
        cursor.execute("SELECT fitbit_user_id, access_token FROM fitbit_users")
        users = cursor.fetchall()
        print(f"Found {len(users)} users to process.")
        
        success_count = 0
        fail_count = 0
        
        for user in users:
            fitbit_user_id, access_token = user
            
            print(f"Processing user: {fitbit_user_id}")
            if update_user_profile(fitbit_user_id, access_token):
                success_count += 1
            else:
                fail_count += 1

    except Exception as e:
        print(f"An error occurred during main process: {e}")
    finally:
        if conn:
            conn.close()
        print("\n--- Job Summary ---")
        print(f"Successful updates: {success_count}")
        print(f"Failed updates: {fail_count}")
        print(f"--- Heart rate zone update job finished at {datetime.now()} ---")


if __name__ == "__main__":
    main()
