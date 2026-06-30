"""
Docker 启动验证脚本
检查所有服务是否正常启动并可以通信

用法:
    python scripts/verification/verify_docker.py

预期:
    1. 后端 API 可达 (/health)
    2. PostgreSQL 可连接
    3. MinIO 可连接
    4. 数据库表已创建
"""

import sys
import time
import urllib.request
import urllib.error


def check_endpoint(url, name, timeout=30, interval=2):
    """检查 HTTP 端点是否可达"""
    print(f"🔍 检查 {name}: {url}")
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(url, timeout=5)
            if resp.status == 200:
                print(f"  ✅ {name} 已就绪 ({int(time.time()-start)}s)")
                return True
        except (urllib.error.URLError, ConnectionError, OSError):
            pass
        print(f"  ⏳ {name} 尚未就绪，重试中...")
        time.sleep(interval)
    print(f"  ❌ {name} 超时 ({timeout}s)")
    return False


def check_postgres(host="db", port=5432, user="postgres", password="password", db="parrotcare", timeout=30):
    """检查 PostgreSQL 连接"""
    print(f"🔍 检查 PostgreSQL: {host}:{port}/{db}")
    try:
        import psycopg2
    except ImportError:
        print("  ⏭️  跳过（psycopg2 未安装）")
        return True

    start = time.time()
    while time.time() - start < timeout:
        try:
            conn = psycopg2.connect(
                host=host, port=port, user=user, password=password, dbname=db
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            conn.close()
            print(f"  ✅ PostgreSQL 已就绪: {version[:30]}...")
            return True
        except Exception:
            pass
        print(f"  ⏳ PostgreSQL 尚未就绪，重试中...")
        time.sleep(2)
    print(f"  ❌ PostgreSQL 超时 ({timeout}s)")
    return False


def check_tables(host="db", port=5432, user="postgres", password="password", db="parrotcare"):
    """检查数据库表是否已创建"""
    print("🔍 检查数据库表...")
    try:
        import psycopg2
    except ImportError:
        print("  ⏭️  跳过（psycopg2 未安装）")
        return True

    try:
        conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=db)
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        if tables:
            print(f"  ✅ 发现 {len(tables)} 个表: {', '.join(tables)}")
            return True
        else:
            print("  ⚠️  表为空（可能需要运行 init_db 或 alembic）")
            return False
    except Exception as e:
        print(f"  ❌ 检查表失败: {e}")
        return False


def main():
    print("=" * 50)
    print("🦜 ParrotCare Docker 启动验证")
    print("=" * 50)
    print()

    results = {}

    # 1. 后端 API
    results["api"] = check_endpoint("http://localhost:8000/health", "后端 API")

    # 2. PostgreSQL
    results["postgres"] = check_postgres()

    # 3. 数据库表
    results["tables"] = check_tables()

    # 4. MinIO
    results["minio"] = check_endpoint("http://localhost:9000/minio/health/live", "MinIO")

    # 5. MinIO Console
    results["minio_console"] = check_endpoint("http://localhost:9001", "MinIO Console")

    print()
    print("=" * 50)
    print("📊 验证结果")
    print("=" * 50)

    all_pass = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print("🎉 所有服务运行正常！")
        return 0
    else:
        print("⚠️  部分服务异常，请检查 docker-compose logs")
        return 1


if __name__ == "__main__":
    sys.exit(main())
