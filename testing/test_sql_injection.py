import os
import sqlite3

def vulnerable_sql_example(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # SQL Injection vulnerability
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    results = cursor.fetchall()
    return results

def command_injection_example(user_input):
    # Command injection vulnerability
    os.system("echo " + user_input)
    
def path_traversal_example(filename):
    # Path traversal vulnerability
    with open("/var/www/files/" + filename) as f:
        content = f.read()
    return content

def insecure_deserialization_example(data):
    # Insecure deserialization vulnerability
    import pickle
    obj = pickle.loads(data)
    return obj