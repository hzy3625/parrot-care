"""
SQLite → PostgreSQL 数据迁移脚本
将现有 SQLite 数据库中的数据导出并导入到 PostgreSQL

用法:
    python scripts/migration/migrate_sqlite_to_pg.py \
        --sqlite-path apps/api/parrotcare.db \
        --pg-url "postgresql://postgres:password@localhost:5432/parrotcare"

或者使用环境变量:
    SQLITE_PATH=apps/api/parrotcare.db \
    PG_URL="postgresql://postgres:password@localhost:5432/parrotcare" \
    python scripts/migration/migrate_sqlite_to_pg.py
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values


def parse_args():
    parser = argparse.ArgumentParser(description="SQLite → PostgreSQL 数据迁移")
    parser.add_argument(
        "--sqlite-path",
        default=os.getenv("SQLITE_PATH", "apps/api/parrotcare.db"),
        help="SQLite 数据库文件路径",
    )
    parser.add_argument(
        "--pg-url",
        default=os.getenv("PG_URL"),
        help="PostgreSQL 连接 URL (例如: postgresql://user:pass@host:5432/db)",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="迁移前清空 PostgreSQL 表（危险！）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只预览不执行",
    )
    return parser.parse_args()


def get_sqlite_tables(sqlite_path):
    """获取 SQLite 中的所有用户表"""
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_sqlite_data(sqlite_path, table):
    """从 SQLite 表中读取所有数据"""
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return columns, [dict(row) for row in rows]


def convert_value(value):
    """转换 SQLite 值为 PostgreSQL 兼容格式"""
    if value is None:
        return None
    if isinstance(value, bytes):
        # SQLite 中的 bytes（如 time 类型）
        return value
    return value


def migrate_table(pg_conn, table, columns, rows, truncate=False, dry_run=False):
    """迁移单个表的数据到 PostgreSQL"""
    if not rows:
        print(f"  [{table}] 无数据，跳过")
        return 0

    cursor = pg_conn.cursor()

    if truncate:
        print(f"  [{table}] 清空现有数据...")
        if not dry_run:
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE")

    col_names = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"

    # 转换数据
    converted_rows = []
    for row in rows:
        converted_row = tuple(convert_value(row.get(col)) for col in columns)
        converted_rows.append(converted_row)

    if dry_run:
        print(f"  [{table}] 预览: {len(rows)} 行 (未执行)")
        return len(rows)

    try:
        execute_values(cursor, insert_sql, converted_rows, page_size=100)
        pg_conn.commit()
        print(f"  [{table}] ✓ 插入 {len(rows)} 行")
        return len(rows)
    except Exception as e:
        pg_conn.rollback()
        print(f"  [{table}] ✗ 失败: {e}")
        raise


def ensure_schema_exists(pg_conn, columns_map):
    """
    确保 PostgreSQL 中存在必要的表结构。
    如果表不存在，尝试创建（基于 SQLAlchemy 模型更可靠）。
    这里我们依赖主应用的 init_db() 来创建表结构。
    """
    pass  # 表结构由主应用的 init_db() 创建


def main():
    args = parse_args()

    sqlite_path = Path(args.sqlite_path)
    if not sqlite_path.exists():
        print(f"❌ SQLite 文件不存在: {sqlite_path}")
        sys.exit(1)

    if not args.pg_url:
        print("❌ 请提供 PostgreSQL 连接 URL (--pg-url 或 PG_URL 环境变量)")
        sys.exit(1)

    print(f"📁 SQLite: {sqlite_path}")
    print(f"🐘 PostgreSQL: {args.pg_url}")
    if args.dry_run:
        print("🔍 模式: Dry Run (不会写入数据)")
    if args.truncate:
        print("⚠️  模式: Truncate (会清空现有数据)")

    # 获取 SQLite 表
    tables = get_sqlite_tables(str(sqlite_path))
    print(f"\n📋 发现 {len(tables)} 个表: {', '.join(tables)}")

    # 连接 PostgreSQL
    try:
        pg_conn = psycopg2.connect(args.pg_url)
        print("✅ PostgreSQL 连接成功")
    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}")
        sys.exit(1)

    total_rows = 0
    try:
        for table in tables:
            columns, rows = get_sqlite_data(str(sqlite_path), table)
            if not rows:
                print(f"  [{table}] 无数据，跳过")
                continue
            count = migrate_table(pg_conn, table, columns, rows, args.truncate, args.dry_run)
            total_rows += count

        print(f"\n✅ 迁移完成! 共处理 {total_rows} 行数据")
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        sys.exit(1)
    finally:
        pg_conn.close()


if __name__ == "__main__":
    main()
