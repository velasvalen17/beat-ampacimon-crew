#!/usr/bin/env python3
import sqlite3
import sys
import os

def analyze(path):
    print(f"\nAnalyzing: {path}")
    if not os.path.exists(path):
        print("  File not found")
        return
    print(f"  Size: {os.path.getsize(path)} bytes")
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()

        # Integrity check
        try:
            cur.execute('PRAGMA integrity_check;')
            res = cur.fetchall()
            print('  PRAGMA integrity_check:')
            for r in res:
                print('   ', r[0])
        except Exception as e:
            print('  integrity_check failed:', e)

        # List tables
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            tables = [r[0] for r in cur.fetchall()]
            print(f'  Tables ({len(tables)}):')
            for t in tables:
                print('   -', t)
            # show row counts for first 10 tables
            for t in tables[:20]:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{t}"')
                    cnt = cur.fetchone()[0]
                    print(f'     {t}: {cnt} rows')
                except Exception as e:
                    print(f'     {t}: count failed ({e})')
        except Exception as e:
            print('  listing tables failed:', e)

        conn.close()
    except sqlite3.DatabaseError as e:
        print('  Database error:', e)
    except Exception as e:
        print('  Error opening DB:', e)


def main():
    if len(sys.argv) < 2:
        print('Usage: analyze_sqlite.py <db-file> [other-db-files]')
        sys.exit(1)
    for p in sys.argv[1:]:
        analyze(p)

if __name__ == '__main__':
    main()
