import os
import sys
import pg8000.dbapi
import requests
import json
import base64
from datetime import datetime, timedelta, timezone

# --- GCP Secret Manager 설정 ---
from google.cloud import secretmanager
from google.api_core.exceptions import NotFound, PermissionDenied

GCP_PROJECT_ID = "api-test-468900" 
SECRET_CLIENT = None

def get_secret(secret_id, version_id="latest"):
    """GCP Secret Manager에서 비밀 값을 가져오는 함수"""
    global SECRET_CLIENT
    if SECRET_CLIENT is None:
        SECRET_CLIENT = secretmanager.SecretManagerServiceClient()
    
    name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
    response = SECRET_CLIENT.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# --- Cloud SQL 설정 ---
from google.cloud.sql.connector import Connector

DB_USER = get_secret("db-user")
DB_PASS = get_secret("db-pass")
DB_NAME = "fitbit_data"
INSTANCE_CONNECTION_NAME = get_secret("db-connection-name")

# Cloud SQL Python Connector 초기화
connector = Connector()

def get_conn():
    """Cloud SQL 데이터베이스 연결을 가져오는 함수"""
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

def refresh_fitbit_token(user_id, current_refresh_token):
    """주어진 리프레시 토큰을 사용하여 Fitbit 액세스 토큰을 갱신하는 함수"""
    print(f"--- Attempting to refresh token for user {user_id} ---")
    
    FITBIT_CLIENT_ID = get_secret("fitbit-client-id")
    FITBIT_CLIENT_SECRET = get_secret("fitbit-client-secret")
    FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
    
    auth_header = base64.b64encode(f"{FITBIT_CLIENT_ID}:{FITBIT_CLIENT_SECRET}".encode()).decode()
    headers = {'Authorization': f'Basic {auth_header}', 'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': current_refresh_token
    }
    
    token_response = requests.post(FITBIT_TOKEN_URL, headers=headers, data=data)
    
    if token_response.status_code == 200:
        new_token_data = token_response.json()
        print("[SUCCESS] Token refreshed successfully.")
        return new_token_data
    else:
        print(f"[ERROR] Failed to refresh token. Status: {token_response.status_code}, Response: {token_response.text}")
        return None

def main():
    """테스트 스크립트의 메인 함수"""
    print("--- Starting Intraday API Test Script ---")
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # 데이터베이스에서 첫 번째 사용자의 정보를 가져옵니다.
        print("Fetching the first user from the database...")
        cursor.execute("SELECT fitbit_user_id, access_token, refresh_token FROM fitbit_users LIMIT 1")
        user = cursor.fetchone()
        
        if not user:
            print("[ERROR] No users found in the database. Please authorize at least one user first.")
            return

        fitbit_user_id, access_token, refresh_token = user
        print(f"Found user: {fitbit_user_id}")
        
        # 테스트를 위해 먼저 토큰을 갱신합니다.
        new_token_data = refresh_fitbit_token(fitbit_user_id, refresh_token)
        if not new_token_data:
            return # 토큰 갱신 실패 시 종료

        access_token = new_token_data['access_token']
        new_refresh_token = new_token_data['refresh_token']

        # 갱신된 토큰을 DB에 저장
        print("Updating tokens in database...")
        cursor.execute(
            "UPDATE fitbit_users SET access_token = %s, refresh_token = %s, updated_at = %s WHERE fitbit_user_id = %s",
            (access_token, new_refresh_token, datetime.now(timezone.utc), fitbit_user_id)
        )
        conn.commit()
        print("Tokens updated successfully in database.")

        # Intraday API 요청을 위한 시간 설정 (어제 전체 데이터)
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
        test_date = yesterday
        start_time = "00:00:00"
        end_time = "23:59:59"

        print(f"Requesting heart rate data for {test_date} (full day, 15min interval)...")

        # Intraday Heart Rate API 엔드포인트 (15분 단위)
        api_url = f"https://api.fitbit.com/1/user/{fitbit_user_id}/activities/heart/date/{test_date}/1d/15min/time/{start_time}/{end_time}.json"
        
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            print("[SUCCESS] Successfully fetched intraday heart rate data!")
            # JSON 응답을 예쁘게 출력합니다.
            print(json.dumps(response.json(), indent=4))
            print("\n--- TEST PASSED ---")
        else:
            print(f"[ERROR] Failed to fetch intraday data. Status: {response.status_code}")
            print("Response Body:")
            print(response.text)
            print("\n--- TEST FAILED ---")

    except Exception as e:
        print(f"[FATAL ERROR] An unexpected error occurred: {e}")
        print("\n--- TEST FAILED ---")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
        print("--- Test Script Finished ---")


if __name__ == "__main__":
    main()
