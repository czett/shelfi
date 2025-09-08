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
        
def get_user_id(username):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        print("Error fetching user ID:", e)
        return None
    finally:
        conn.close()
        
def get_user_spaces(user_id):
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.space_id, s.space_name, COUNT(us2.user_id) as member_count
                FROM spaces s
                JOIN user_spaces us ON s.space_id = us.space_id
                JOIN user_spaces us2 ON s.space_id = us2.space_id
                WHERE us.user_id = %s
                GROUP BY s.space_id, s.space_name
            """, (user_id,))
            spaces = cur.fetchall()
            return [{'id': row[0], 'name': row[1], 'members': row[2]} for row in spaces]
    except Exception as e:
        print("Error fetching user spaces:", e)
        return []
    finally:
        conn.close()

def create_space(user_id, space_name):
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with conn.cursor() as cur:
            # Create new space
            cur.execute("INSERT INTO spaces (space_name) VALUES (%s) RETURNING space_id", (space_name,))
            space_id = cur.fetchone()[0]
            # Associate space with user
            cur.execute("INSERT INTO user_spaces (user_id, space_id) VALUES (%s, %s)", (user_id, space_id))
            conn.commit()
            return True, "Space created successfully."
    except Exception as e:
        print("Error creating space:", e)
        return False, "An error occurred while creating the space."
    finally:
        conn.close()