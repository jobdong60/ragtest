import os
import base64
import requests
import pg8000.dbapi
import sys
from datetime import datetime, timedelta
from google.cloud import secretmanager
from google.cloud.sql.connector import Connector

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

# --- 데이터 수집 로직 ---

def refresh_token_for_user(refresh_token):
    """주어진 refresh_token으로 새로운 access_token을 발급받습니다."""
    auth_header = base64.b64encode(f"{FITBIT_CLIENT_ID}:{FITBIT_CLIENT_SECRET}".encode()).decode()
    headers = {'Authorization': f'Basic {auth_header}', 'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    response = requests.post(FITBIT_TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Token refresh failed for token starting with {refresh_token[:5]}...: {response.text}")
        return None

def fetch_and_store_data(user_id, access_token):
    """Fitbit API에서 오늘의 요약 데이터를 가져와 데이터베이스에 저장합니다."""
    headers = {'Authorization': f'Bearer {access_token}'}
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    summary_endpoint = f"{FITBIT_API_BASE_URL}/1/user/-/activities/date/{today_str}.json"
    
    try:
        response = requests.get(summary_endpoint, headers=headers)
        response.raise_for_status()

        summary = response.json().get("summary", {})
        steps = summary.get("steps", 0)
        distance_info = next((d for d in summary.get("distances", []) if d.get("activity") == "total"), {})
        distance = distance_info.get("distance", 0.0)
        calories = summary.get("caloriesOut", 0)
        resting_heart_rate = summary.get("restingHeartRate", None)

        # 심박수 구간별 상세 데이터 추출
        heart_rate_zones = summary.get("heartRateZones", [])
        zone_data = {
            'Out of Range': {'minutes': 0, 'min': 0, 'max': 0},
            'Fat Burn': {'minutes': 0, 'min': 0, 'max': 0},
            'Cardio': {'minutes': 0, 'min': 0, 'max': 0},
            'Peak': {'minutes': 0, 'min': 0, 'max': 0}
        }
        for zone in heart_rate_zones:
            zone_name = zone.get("name")
            if zone_name in zone_data:
                zone_data[zone_name]['minutes'] = zone.get("minutes", 0)
                zone_data[zone_name]['min'] = zone.get("min", 0)
                zone_data[zone_name]['max'] = zone.get("max", 0)

        print(f"User {user_id}: Steps={steps}, Distance={distance} km, Calories={calories}, Resting HR={resting_heart_rate}")
        print(f"--> HR Zones: Peak={zone_data['Peak']['minutes']}m ({zone_data['Peak']['min']}-{zone_data['Peak']['max']}), Cardio={zone_data['Cardio']['minutes']}m, Fat Burn={zone_data['Fat Burn']['minutes']}m")
        
        # 중복 방지 데이터 저장 (UPSERT)
        conn = get_conn()
        cursor = conn.cursor()
        
        upsert_sql = """
            INSERT INTO daily_summaries (
                fitbit_user_id, date, steps, distance, calories, resting_heart_rate, 
                hr_zone_out_of_range_minutes, hr_zone_fat_burn_minutes, 
                hr_zone_cardio_minutes, hr_zone_peak_minutes, 
                hr_zone_fat_burn_min_hr, hr_zone_fat_burn_max_hr,
                hr_zone_cardio_min_hr, hr_zone_cardio_max_hr,
                hr_zone_peak_min_hr, hr_zone_peak_max_hr,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (fitbit_user_id, date) 
            DO UPDATE SET
                steps = EXCLUDED.steps,
                distance = EXCLUDED.distance,
                calories = EXCLUDED.calories,
                resting_heart_rate = EXCLUDED.resting_heart_rate,
                hr_zone_out_of_range_minutes = EXCLUDED.hr_zone_out_of_range_minutes,
                hr_zone_fat_burn_minutes = EXCLUDED.hr_zone_fat_burn_minutes,
                hr_zone_cardio_minutes = EXCLUDED.hr_zone_cardio_minutes,
                hr_zone_peak_minutes = EXCLUDED.hr_zone_peak_minutes,
                hr_zone_fat_burn_min_hr = EXCLUDED.hr_zone_fat_burn_min_hr,
                hr_zone_fat_burn_max_hr = EXCLUDED.hr_zone_fat_burn_max_hr,
                hr_zone_cardio_min_hr = EXCLUDED.hr_zone_cardio_min_hr,
                hr_zone_cardio_max_hr = EXCLUDED.hr_zone_cardio_max_hr,
                hr_zone_peak_min_hr = EXCLUDED.hr_zone_peak_min_hr,
                hr_zone_peak_max_hr = EXCLUDED.hr_zone_peak_max_hr,
                updated_at = EXCLUDED.updated_at;
        """
        cursor.execute(upsert_sql, (
            user_id, today_str, steps, distance, calories, resting_heart_rate,
            zone_data['Out of Range']['minutes'], zone_data['Fat Burn']['minutes'], 
            zone_data['Cardio']['minutes'], zone_data['Peak']['minutes'],
            zone_data['Fat Burn']['min'], zone_data['Fat Burn']['max'],
            zone_data['Cardio']['min'], zone_data['Cardio']['max'],
            zone_data['Peak']['min'], zone_data['Peak']['max'],
            datetime.now()
        ))
        conn.commit()
        print(f"Successfully saved summary for user {user_id} on {today_str}.")
        cursor.close()
        conn.close()
        
    except requests.exceptions.HTTPError as e:
        print(f"Failed to fetch summary data for user {user_id}: {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred during data fetch/store for user {user_id}: {e}")


def main():
    """메인 실행 함수"""
    print(f"--- Starting data collection job at {datetime.now()} ---")
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, fitbit_user_id, refresh_token FROM fitbit_users")
        users = cursor.fetchall()
        print(f"Found {len(users)} users to process.")
        
        for user in users:
            db_id, fitbit_user_id, old_refresh_token = user
            
            print(f"Processing user: {fitbit_user_id}")
            new_token_data = refresh_token_for_user(old_refresh_token)
            
            if new_token_data:
                new_access_token = new_token_data['access_token']
                new_refresh_token = new_token_data['refresh_token']
                
                update_sql = "UPDATE fitbit_users SET access_token = %s, refresh_token = %s, updated_at = %s WHERE id = %s"
                cursor.execute(update_sql, (new_access_token, new_refresh_token, datetime.now(), db_id))
                conn.commit()
                
                fetch_and_store_data(fitbit_user_id, new_access_token)
            else:
                print(f"Skipping data fetch for user {user_id} due to token refresh failure.")

    except Exception as e:
        print(f"An error occurred during main process: {e}")
    finally:
        if conn:
            conn.close()
        print(f"--- Data collection job finished at {datetime.now()} ---")


if __name__ == "__main__":
    main()
