#!/usr/bin/env python3
"""Cloud SQL에서 로컬 PostgreSQL로 데이터만 복사"""

import psycopg2
from google.cloud.sql.connector import Connector
from google.cloud import secretmanager

# GCP Secret Manager 설정
GCP_PROJECT_ID = "api-test-468900"
SECRET_CLIENT = secretmanager.SecretManagerServiceClient()

def get_secret(secret_id):
    name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = SECRET_CLIENT.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

# Cloud SQL 연결
print("Connecting to Cloud SQL...")
connector = Connector()
cloud_conn = connector.connect(
    get_secret("db-connection-name"),
    "pg8000",
    user=get_secret("db-user"),
    password=get_secret("db-pass"),
    db="fitbit_data"
)
cloud_cursor = cloud_conn.cursor()

# 로컬 PostgreSQL 연결
print("Connecting to local PostgreSQL...")
local_conn = psycopg2.connect(
    host="localhost",
    database="fitbit_data",
    user="fitbit_user",
    password="fitbit_password"
)
local_cursor = local_conn.cursor()

# 복사할 테이블 목록 (Django 앱 관련 테이블만)
tables_to_copy = ['fitbit_users', 'daily_summaries']

for table in tables_to_copy:
    print(f"\nCopying data from {table}...")

    # Cloud SQL에서 데이터 가져오기
    cloud_cursor.execute(f"SELECT * FROM {table}")
    rows = cloud_cursor.fetchall()

    if not rows:
        print(f"  No data in {table}")
        continue

    # 컬럼 이름 가져오기
    col_names = [desc[0] for desc in cloud_cursor.description]

    # 로컬 DB에 삽입
    placeholders = ', '.join(['%s'] * len(col_names))
    insert_sql = f"INSERT INTO {table} ({', '.join(col_names)}) VALUES ({placeholders})"

    try:
        local_cursor.executemany(insert_sql, rows)
        local_conn.commit()
        print(f"  ✓ Copied {len(rows)} rows")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        local_conn.rollback()

# 시퀀스 재설정
print("\nResetting sequences...")
for table in tables_to_copy:
    try:
        local_cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1), false)")
        local_conn.commit()
        print(f"  ✓ Reset sequence for {table}")
    except Exception as e:
        print(f"  ✗ Could not reset sequence for {table}: {e}")

print("\n✓ Data migration completed!")

cloud_cursor.close()
cloud_conn.close()
local_cursor.close()
local_conn.close()
