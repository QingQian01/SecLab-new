import pymysql
import json

conn = pymysql.connect(
    host='localhost', port=3306,
    user='seclab_app', password='Seclab@123',
    database='seclab_profile', charset='utf8mb4'
)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# Check table structure
cursor.execute('DESCRIBE student_profile_snapshot')
print("=== student_profile_snapshot columns ===")
for row in cursor.fetchall():
    print(f"  {row['Field']:30s} {row['Type']}")

# Get latest snapshot
cursor.execute(
    'SELECT * FROM student_profile_snapshot '
    'WHERE user_id=5 ORDER BY created_at DESC LIMIT 1'
)
row = cursor.fetchone()
if row:
    print(f"\n=== Latest snapshot for user 5 ===")
    print(f"  snapshot_id: {row.get('snapshot_id')}")
    print(f"  created_at:  {row.get('created_at')}")
    # Find the JSON column
    for key in row:
        val = row[key]
        if isinstance(val, str) and ('recommend' in val.lower() or '知识' in val or '鐭' in val):
            print(f"\n  Column '{key}' contains recommendation data:")
            try:
                data = json.loads(val)
                recs = data.get('recommendations', [])
                print(f"  Found {len(recs)} recommendations")
                for rec in recs[:2]:
                    reason = rec.get('reason', '')
                    print(f"    reason: {reason[:150]}")
                    has_katakana = any('\u30c0' <= c <= '\u30ff' for c in reason)
                    print(f"    has_katakana_garble: {has_katakana}")
            except:
                print(f"  Raw (first 200 chars): {val[:200]}")
            break
else:
    print("No snapshot found for user 5")

conn.close()
