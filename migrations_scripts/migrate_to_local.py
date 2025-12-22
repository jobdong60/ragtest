#!/usr/bin/env python3
"""Cloud SQL에서 로컬 PostgreSQL로 데이터 마이그레이션"""

import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path
from myhealth.settings import get_conn, DB_USER, DB_PASS, DB_NAME

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

# Cloud SQL 연결
print("Connecting to Cloud SQL...")
cloud_conn = get_conn()
cloud_cursor = cloud_conn.cursor()

# 로컬 PostgreSQL 연결
print("Connecting to local PostgreSQL...")
local_conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    database=os.getenv('DB_NAME', 'fitbit_data'),
    user=os.getenv('DB_USER', 'fitbit_user'),
    password=os.getenv('DB_PASSWORD', '')
)
local_conn.autocommit = False
local_cursor = local_conn.cursor()

# 테이블 목록 가져오기
cloud_cursor.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name
""")
tables = [row[0] for row in cloud_cursor.fetchall()]

print(f"\nFound {len(tables)} tables to migrate:")
for table in tables:
    print(f"  - {table}")

# 각 테이블의 스키마와 데이터 복사
for table in tables:
    print(f"\nMigrating table: {table}")

    # 1. 테이블 스키마 가져오기
    cloud_cursor.execute(f"""
        SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
    """)
    columns = cloud_cursor.fetchall()

    # 2. CREATE TABLE 문 생성
    create_parts = []
    for col_name, data_type, max_length, nullable, default in columns:
        col_def = f"{col_name} "

        if data_type == 'character varying':
            col_def += f"VARCHAR({max_length})" if max_length else "VARCHAR"
        elif data_type == 'timestamp with time zone':
            col_def += "TIMESTAMPTZ"
        elif data_type == 'timestamp without time zone':
            col_def += "TIMESTAMP"
        elif data_type == 'USER-DEFINED':
            col_def += "TEXT"  # enum이나 custom type은 TEXT로
        else:
            col_def += data_type.upper()

        if nullable == 'NO':
            col_def += " NOT NULL"

        if default:
            col_def += f" DEFAULT {default}"

        create_parts.append(col_def)

    # 기본 키 및 제약조건 가져오기
    cloud_cursor.execute(f"""
        SELECT constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name = '{table}' AND constraint_type IN ('PRIMARY KEY', 'UNIQUE')
    """)
    constraints = cloud_cursor.fetchall()

    for const_name, const_type in constraints:
        cloud_cursor.execute(f"""
            SELECT column_name
            FROM information_schema.key_column_usage
            WHERE constraint_name = '{const_name}' AND table_name = '{table}'
            ORDER BY ordinal_position
        """)
        const_cols = [row[0] for row in cloud_cursor.fetchall()]

        if const_type == 'PRIMARY KEY':
            create_parts.append(f"PRIMARY KEY ({', '.join(const_cols)})")
        elif const_type == 'UNIQUE':
            create_parts.append(f"UNIQUE ({', '.join(const_cols)})")

    create_sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(create_parts)})"

    try:
        local_cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        local_cursor.execute(create_sql)
        print(f"  ✓ Created table structure")
    except Exception as e:
        print(f"  ✗ Error creating table: {e}")
        continue

    # 3. 데이터 복사
    cloud_cursor.execute(f"SELECT * FROM {table}")
    rows = cloud_cursor.fetchall()

    if rows:
        col_names = [desc[0] for desc in cloud_cursor.description]
        placeholders = ', '.join(['%s'] * len(col_names))
        insert_sql = f"INSERT INTO {table} ({', '.join(col_names)}) VALUES ({placeholders})"

        try:
            local_cursor.executemany(insert_sql, rows)
            print(f"  ✓ Copied {len(rows)} rows")
        except Exception as e:
            print(f"  ✗ Error copying data: {e}")
            local_conn.rollback()
            continue
    else:
        print(f"  ✓ No data to copy")

    local_conn.commit()

# 시퀀스 재설정
print("\nResetting sequences...")
local_cursor.execute("""
    SELECT 'SELECT SETVAL(' ||
           quote_literal(quote_ident(sequence_namespace.nspname) || '.' || quote_ident(class_sequence.relname)) ||
           ', COALESCE(MAX(' ||quote_ident(pg_attribute.attname)|| '), 1) ) FROM ' ||
           quote_ident(table_namespace.nspname)|| '.'||quote_ident(class_table.relname)|| ';'
    FROM pg_depend
    INNER JOIN pg_class AS class_sequence ON class_sequence.oid = pg_depend.objid
    INNER JOIN pg_class AS class_table ON class_table.oid = pg_depend.refobjid
    INNER JOIN pg_attribute ON pg_attribute.attrelid = class_table.oid AND pg_attribute.attnum = pg_depend.refobjsubid
    INNER JOIN pg_namespace as table_namespace ON table_namespace.oid = class_table.relnamespace
    INNER JOIN pg_namespace AS sequence_namespace ON sequence_namespace.oid = class_sequence.relnamespace
    WHERE class_sequence.relkind = 'S'
""")
for row in local_cursor.fetchall():
    try:
        local_cursor.execute(row[0])
    except:
        pass

local_conn.commit()

print("\n✓ Migration completed successfully!")

cloud_cursor.close()
cloud_conn.close()
local_cursor.close()
local_conn.close()
