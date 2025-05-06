# generate_sql_injection_test.py

sql_injections = [
    "' OR '1'='1",
    "' OR 1=1 --",
    "'; DROP TABLE users; --",
    "' UNION SELECT * FROM users --",
    "' AND (SELECT COUNT(*) FROM users) > 0 --",
    "' OR 'abc' = 'abc",
    "' OR 1=1 LIMIT 1 --",
    "' OR sleep(5) --",
    "' AND EXISTS(SELECT * FROM users) --",
    "'; EXEC xp_cmdshell('dir'); --"
]

# Create a test file with 500 lines of SQL injection
with open("sql_injection_test_code.txt", "w") as f:
    for i in range(500):
        payload = sql_injections[i % len(sql_injections)]
        f.write(f"query = \"SELECT * FROM users WHERE username = '{payload}'\"\n")
