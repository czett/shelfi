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

# General auth return Scheme:
# (success: bool, message: str)

def login(username, password):
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
            if not result:
                return False, "Username not found."
            if bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
                return True, "Login successful."
            else:
                return False, "Incorrect password."
    except Exception as e:
        print("Error during login:", e)
        return False, "An error occurred during login."
    finally:
        conn.close()
        
def register(username, password, email):
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with conn.cursor() as cur:
            # Check if username or email already exists
            cur.execute("SELECT 1 FROM users WHERE username = %s OR email = %s", (username, email))
            if cur.fetchone():
                return False, "Username or email already exists."
            cur.execute("INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)", 
                        (username, hashed_password, email))
            conn.commit()
            return True, "Registration successful."
    except Exception as e:
        print("Error during registration:", e)
        return False, "An error occurred during registration."
    finally:
        conn.close()