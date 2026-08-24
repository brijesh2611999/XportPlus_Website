import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    # Attempt to connect to the NeonDB Postgres instance
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found in .env file.")
    return psycopg2.connect(database_url)

def save_cma_tokens(cookie_string: str, csrf_token: str):
    """
    Saves the CMA-CGM tokens to the site_tokens table, mimicking the Node.js implementation.
    """
    import json
    token_payload = json.dumps({"CMA_COOKIE": cookie_string, "CMA_XSRF_TOKEN": csrf_token})
    
    upsert_query = """
        INSERT INTO site_tokens (site_name, token_data, last_updated)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (site_name)
        DO UPDATE SET token_data = EXCLUDED.token_data, last_updated = CURRENT_TIMESTAMP;
    """
    
    print(f"Saving CMA-CGM tokens to database...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(upsert_query, ('CMA-CGM', token_payload))
        conn.commit()
        cursor.close()
        conn.close()
        print("Successfully saved CMA-CGM tokens to DB via Python!")
    except Exception as e:
        print(f"Database Error: {e}")

def get_cma_tokens():
    """
    Retrieves the active CMA-CGM tokens from the site_tokens table.
    Returns a dictionary or None if not found.
    """
    import json
    
    query = "SELECT token_data FROM site_tokens WHERE site_name = 'CMA-CGM';"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0]:
            # psycopg2 automatically parses JSON/JSONB columns into dicts
            return result[0] if isinstance(result[0], dict) else json.loads(result[0])
        return None
    except Exception as e:
        print(f"Database Error: {e}")
        return None
