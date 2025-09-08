import psycopg
import dotenv, os
import bcrypt

try:
    dotenv.load_dotenv()
except Exception as e:
    # Vercel
    print("No .env file found, proceeding with system environment variables.")
    
db_string = os.getenv("DB_STRING")

def get_db_connection():
    try:
        conn = psycopg.connect(db_string)
        return conn
    except Exception as e:
        print("Error connecting to the database:", e)
        return None