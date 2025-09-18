import psycopg
import dotenv, os, requests
import bcrypt
from datetime import datetime

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
        
def get_username(user_id):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        print("Error fetching username:", e)
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
            cur.execute("INSERT INTO user_spaces (user_id, space_id, role) VALUES (%s, %s, %s)", (user_id, space_id, "admin"))
            conn.commit()
            return True, "Space created successfully."
    except Exception as e:
        print("Error creating space:", e)
        return False, "An error occurred while creating the space."
    finally:
        conn.close()

def is_user_in_space(user_id, space_id):
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM user_spaces WHERE user_id = %s AND space_id = %s", (user_id, space_id))
            result = cur.fetchone()
            return result is not None
    except Exception as e:
        print("Error checking if user is in space:", e)
        return False
    finally:
        conn.close()
        
def get_space_details(space_id):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    s.space_id, 
                    s.space_name, 
                    COUNT(us.user_id) as member_count,
                    u.username as creator_username,
                    s.created_at
                FROM spaces s
                LEFT JOIN user_spaces us ON s.space_id = us.space_id
                LEFT JOIN user_spaces admin_us ON s.space_id = admin_us.space_id AND admin_us.role = 'admin'
                LEFT JOIN users u ON admin_us.user_id = u.user_id
                WHERE s.space_id = %s
                GROUP BY s.space_id, s.space_name, u.username, s.created_at
            """, (space_id,))
            result = cur.fetchone()
            if result:
                created_at_date = result[4]
                if isinstance(created_at_date, datetime):
                    created_at_date = created_at_date.strftime("%b %d, %Y")
                else:
                    created_at_date = str(created_at_date)
                return {
                    'id': result[0],
                    'name': result[1],
                    'members': result[2],
                    'creator': result[3],
                    'created_at': created_at_date
                }
            return None
    except Exception as e:
        print("Error fetching space details:", e)
        return None
    finally:
        conn.close()
        
def get_space_items(space_id):
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT item_id, product_name, quantity, unit, barcode, image_url, expiration_date, added_by_user_id
                FROM items
                WHERE space_id = %s
            """, (space_id,))
            items = cur.fetchall()
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'quantity': row[2],
                    'unit': row[3],
                    'barcode': row[4],
                    'image_url': row[5],
                    'expiration_date': row[6],
                    'added_by_user': row[7],
                }
                for row in items
            ]
    except Exception as e:
        print("Error fetching space items:", e)
        return []
    finally:
        conn.close()
        
def add_item_to_shopping_list(space_id, user_id, item_name):
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO shopping_list (space_id, added_by_user_id, product_name)
                VALUES (%s, %s, %s)
                RETURNING list_item_id;
            """, (space_id, user_id, item_name))
            new_id = cur.fetchone()[0]
            conn.commit()
            return True, {"id": new_id}
    except Exception as e:
        print("Error adding item to shopping list:", e)
        return False, str(e)
    finally:
        conn.close()
        
def get_shopping_list(space_id):
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT list_item_id, space_id, product_name, added_by_user_id, created_at, checked, visible
                FROM shopping_list
                WHERE space_id = %s
                ORDER BY checked, created_at DESC
            """, (space_id,))
            items = cur.fetchall()
            return [
                {
                    'list_item_id': row[0],
                    'space_id': row[1],
                    'product_name': row[2],
                    'added_by_user_id': row[3],
                    'created_at': row[4],
                    'checked': row[5],
                    'visible': row[6]
                }
                for row in items
            ]
    except Exception as e:
        print("Error fetching shopping list:", e)
        return []
    finally:
        conn.close()

def toggle_shopping_list_item(list_item_id):
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE shopping_list
                SET checked = NOT checked
                WHERE list_item_id = %s
            """, (list_item_id,))
            conn.commit()
            return True, "Item toggled."
    except Exception as e:
        print("Error toggling item:", e)
        return False, "An error occurred while toggling the item."
    finally:
        conn.close()

def add_item_to_space_list(space_id, user_id, item_name, date, amount, unit):
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO items (space_id, added_by_user_id, product_name, expiration_date, quantity, unit)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (space_id, user_id, item_name, date, amount, unit))
            conn.commit()
            return True, "Item added to space list."
    except Exception as e:
        print("Error adding item to space list:", e)
        return False, "An error occurred while adding the item."
    finally:
        conn.close()

def get_space_items(space_id):
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT item_id, product_name, quantity, unit, barcode, image_url, expiration_date, added_by_user_id, barcode, image_url
                FROM items
                WHERE space_id = %s
            """, (space_id,))
            items = cur.fetchall()
            return [
                {
                    'id': row[0],
                    'name': row[1],
                    # quantity as int
                    'quantity': int(row[2]),
                    'unit': row[3],
                    'barcode': row[4],
                    'image_url': row[5],
                    'expiration_date': row[6],
                    'added_by_user': row[7],
                    'barcode': row[8],
                    'image_url': row[9]
                }
                for row in items
            ]
    except Exception as e:
        print("Error fetching space items:", e)
        return []
    finally:
        conn.close()

def modify_item_amount(item_id, amount):
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE items
                SET quantity = %s
                WHERE item_id = %s
            """, (amount, item_id))
            conn.commit()
            return True, "Item quantity modified."
    except Exception as e:
        print("Error modifying item quantity:", e)
        return False, "An error occurred while modifying the item quantity."
    finally:
        conn.close()

def clear_shopping_list(space_id):
    conn = get_db_connection()
    # set visible to false for all checked items in shopping_list table
    if conn is None:
        return False, "Database connection failed."
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE shopping_list
                SET visible = FALSE
                WHERE space_id = %s and checked = TRUE
            """, (space_id,))
            conn.commit()
            return True, "Shopping list cleared."
    except Exception as e:
        print("Error clearing shopping list:", e)
        return False, "An error occurred while clearing the shopping list."
    finally:
        conn.close()

def get_product_info_from_barcode(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == 1:
                product_info = data['product']
                
                # Extract product name
                product_name = product_info.get('product_name_en', product_info.get('product_name', 'Name not found'))
                
                # Extract photo URL
                image_url = product_info.get('image_front_url', 'Photo not found')
                
                # Extract quantity and unit
                quantity = product_info.get('quantity', 'Quantity not found')
                
                return {
                    "name": product_name,
                    "photo": image_url,
                    "quantity": quantity
                }
            else:
                return {"error": "Product not found."}
        else:
            return {"error": f"API request failed. Status code: {response.status_code}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {e}"}