from flask import Flask, render_template, redirect, session, request, jsonify
import database, dotenv, os, re, random, string
from datetime import datetime

try:
    dotenv.load_dotenv()
except Exception as e:
    # Vercel
    print("No .env file found, proceeding with system environment variables.")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

def check_logged_in():
    return session.get('logged_in', False)

@app.route('/')
def index():
    if check_logged_in():
        return redirect('/dashboard')
    
    # redirect to auth page if not logged in, as there is no landing page planned. this is NOT SaaS
    return redirect('/login')
    
    return render_template('index.html', session=session)

@app.route('/login')
def login():
    if check_logged_in():
        return redirect('/')
    return render_template('auth.html', action='login', session=session)

@app.route('/register')
def register():
    if check_logged_in():
        return redirect('/')
    return render_template('auth.html', action='register', session=session)

@app.route('/login/submit', methods=['POST'])
def login_submit():
    username = request.form['username']
    username = username.lower()
    password = request.form['password']
    
    # Sanitize username: allow only alphanumeric and underscores, reject others
    if not re.match(r'^\w+$', username):
        return render_template('auth.html', action='login', message='Invalid username: only letters, numbers, and underscores are allowed.', session=session)
    
    success, message = database.login(username, password)

    if success:
        session['username'] = username
        session['logged_in'] = True

        # get user id as well
        user_id = database.get_user_id(username)
        session['user_id'] = user_id

        return redirect('/dashboard')
    else:
        return render_template('auth.html', action='login', message=message, session=session)
    
@app.route('/register/submit', methods=['POST'])
def register_submit():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    success, message = database.register(username, password, email)
    if success:
        session['username'] = username
        session['logged_in'] = True

        # get user id as well
        user_id = database.get_user_id(username)
        session['user_id'] = user_id

        return redirect('/dashboard')
    else:
        return render_template('auth.html', action='register', message=message, session=session)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if not check_logged_in():
        return redirect('/login')
    
    # fetch spaces of logged in user
    user_id = session.get('user_id')
    spaces = database.get_user_spaces(user_id)
    
    return render_template('dashboard.html', session=session, spaces=spaces)

@app.route('/api/create-space', methods=['GET', 'POST'])
def create_space():
    if not check_logged_in():
        return redirect('/login')
    
    user_id = session.get('user_id')
    space_name = request.values.get('space_name')
    if space_name:
        space_name = space_name.capitalize()
    
    if not space_name or len(space_name) > 100:
        return "Invalid space name.", 400
    
    success, message = database.create_space(user_id, space_name)
    if success:
        return redirect('/dashboard')
    else:
        return message, 500
    
@app.route("/space/<int:space_id>")
def view_space(space_id):
    if not check_logged_in():
        return redirect('/login')
    
    # check if user is in space
    if not database.is_user_in_space(session.get('user_id'), space_id):
        return redirect('/dashboard')
    
    space = database.get_space_details(space_id)
    
    session['current_space_id'] = space_id
    
    # get shopping list
    shopping_list = database.get_shopping_list(space_id)
    for item in shopping_list:
        # user_id = item.get('added_by_user_id')
        # Get username from user_id
        # item['username'] = database.get_username(user_id)
        
        if item.get('created_at'):
            try:
                # Assume item['created_at'] is a SQL timestamp (string or float)
                if isinstance(item['created_at'], (int, float)):
                    dt = datetime.fromtimestamp(item['created_at'])
                else:
                    # Try parsing as string
                    dt = datetime.fromisoformat(str(item['created_at']))
                item['created_at'] = dt.strftime('%b %d, %Y')
            except Exception:
                pass

    # get items in space
    items = database.get_space_items(space_id)
    #if expiration date is defined for an item in get items dict, add another key with info: expires in x days, but only the amount of days it will take to reach the stored and initially passed date.
    if items:
        for item in items:
            if item.get('expiration_date'):
                try:
                    # Assume item['created_at'] is a SQL timestamp (string or float)
                    if isinstance(item['expiration_date'], (int, float)):
                        dt = datetime.fromtimestamp(item['expiration_date'])
                    else:
                        # Try parsing as string
                        dt = datetime.fromisoformat(str(item['expiration_date']))
                    item['readable_expiration_date'] = dt.strftime('%b %d, %Y')
                except Exception:
                    pass

    num_expired = 0
    num_expiring_soon = 0

    # determine items that expire soon or are expired
    for item in items:
        if item.get('expiration_date'):
            try:
                # if expiration date is defined, assume the item is expired if current date if after expiration date OR save item as expiring soon if date is less than 3 days in the future
                # first, check for already expired items
                if datetime.now() > item['expiration_date']:
                    num_expired += 1
                else:
                    # check if expiration date is less than 3 days in the future
                    if datetime.now() + timedelta(days=3) > item['expiration_date']:
                        num_expiring_soon += 1
            except Exception:
                pass

    return render_template('space.html', session=session, space=space, items=items, shopping_list=shopping_list, num_expired=num_expired, num_expiring_soon=num_expiring_soon)

@app.route("/api/add-to-shopping-list", methods=['POST'])
def add_to_shopping_list():
    if not check_logged_in():
        return redirect('/login')
    
    item_name = request.form.get('item_name')
    if item_name:
        item_name = item_name.capitalize()
        
    space_id = session.get('current_space_id')
    user_id = session.get('user_id')
    
    if not space_id or not item_name or len(item_name) > 100:
        return "Invalid input.", 400
    
    success, message = database.add_item_to_shopping_list(space_id, user_id, item_name)
    
    if success:
        return redirect(f'/space/{space_id}')
    else:
        return message, 500

@app.route("/api/toggle-shopping-list-item/<item_id>", methods=['POST'])
def toggle_shopping_list_item(item_id):
    if not check_logged_in():
        return jsonify({"success": False, "message": "You are not logged in."})
        return redirect('/login')
    
    success, message = database.toggle_shopping_list_item(item_id)
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": message})

    if success:
        return redirect(f'/space/{session.get("current_space_id")}')
    else:
        return message, 500
    
@app.route("/api/add-to-space-list", methods=['POST'])
def add_item_to_space_list():
    if not check_logged_in():
        return jsonify({"success": False, "message": "You are not logged in."}), 401

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid JSON"}), 400

    item_name = data.get("item_name", "").strip()
    expiration_date = data.get("expiration_date") or None
    amount = data.get("amount")
    unit = data.get("unit")
    space_id = session.get('current_space_id')
    user_id = session.get('user_id')

    if not space_id or not item_name or not amount or not unit or len(item_name) > 100:
        return jsonify({"success": False, "message": "Invalid input."}), 400

    # DB-Funktion gibt jetzt direkt die neue ID zurück
    success, message, new_id = database.add_item_to_space_list(
        space_id, user_id, item_name, expiration_date, amount, unit
    )

    if success:
        readable_exp = None
        if expiration_date:
            try:
                readable_exp = datetime.fromisoformat(expiration_date).strftime('%b %d, %Y')
            except Exception:
                pass

        return jsonify({
            "success": True,
            "item": {
                "id": new_id,
                "name": item_name,
                "quantity": amount,
                "unit": unit,
                "readable_expiration_date": readable_exp
            }
        })
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route("/api/modify-item-amount/<int:item_id>", methods=["POST"])
def modify_item_amount(item_id):
    if not check_logged_in():
        return jsonify({"success": False, "message": "You are not logged in."}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "Invalid JSON"}), 400

    try:
        new_amount = int(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid amount"}), 400

    success, message = database.modify_item_amount(item_id, new_amount)

    if success:
        # Optional: zurückgeben, wie das Item jetzt aussieht
        item = database.get_item_by_id(item_id)
        readable_exp = None
        if item.get("expiration_date"):
            try:
                readable_exp = item["expiration_date"].strftime("%b %d, %Y")
            except Exception:
                readable_exp = str(item["expiration_date"])

        return jsonify({
            "success": True,
            "item": {
                "id": item_id,
                "name": item.get("name"),
                "quantity": item.get("quantity"),
                "unit": item.get("unit"),
                "readable_expiration_date": readable_exp
            }
        })
    else:
        return jsonify({"success": False, "message": message}), 500

@app.route("/api/clear-shopping-list", methods=['POST'])
def clear_shopping_list():
    if not check_logged_in():
        return jsonify({'success': False, 'message': 'You are not logged in.'})
        return redirect('/login')
    
    space_id = session.get('current_space_id')
    
    success, message = database.clear_shopping_list(space_id)
    
    # return json format, as this is an api for the js in frontend
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': message})

    if success:
        return redirect(f'/space/{space_id}')
    else:
        return message, 500
    
@app.route("/api/add-item-to-shopping-list", methods=['POST'])
def add_item_to_shopping_list():
    if not check_logged_in():
        return jsonify({"success": False, "message": "You are not logged in."}), 401
    
    data = request.get_json()
    item_name = data.get("item_name", "").strip().capitalize()
    space_id = session.get("current_space_id")
    user_id = session.get("user_id")

    if not space_id or not item_name or len(item_name) > 100:
        return jsonify({"success": False, "message": "Invalid input."}), 400

    success, result = database.add_item_to_shopping_list(space_id, user_id, item_name)
    
    if success:
        return jsonify({
            "success": True,
            "item": {
                "list_item_id": result["id"],
                "product_name": item_name,
                "username": session["username"],
                "created_at": datetime.now().strftime("%b %d, %Y")
            }
        })
    else:
        return jsonify({"success": False, "message": result}), 500

@app.route("/api/create-invitation", methods=['POST'])
def create_invitation():
    if not check_logged_in():
        return jsonify({"success": False, "message": "You are not logged in."}), 401
    
    # fetch user_id from session, so logged in user
    # fetch space id from json query as one user might be in multiple spaces and only wants to create an invite for one
    data = request.get_json()
    user_id = session.get('user_id')
    space_id = data.get("space_id")

    if not space_id or not user_id or not data:
        return jsonify({"success": False, "message": "Invalid input."}), 400

    success, message, result = database.create_invitation_code(user_id, space_id)
    if success:
        return jsonify({
            "success": True,
            "invitation": {
                "id": result[0],
                "code": result[1]
            }
        })
    else:
        return jsonify({"success": False, "message": message})

@app.route("/api/handle-invitation", methods=['POST'])
def handle_invitation_route():
    if not check_logged_in():
        return jsonify({"success": False, "message": "You are not logged in."}), 401
    
    data = request.get_json()
    user_id = session.get('user_id')
    invitation_code = data.get("invitation_code")
    
    if not invitation_code or not user_id:
        return jsonify({"success": False, "message": "Invalid input."}), 400
    
    success, message, result = database.handle_invitation(user_id, invitation_code)

    if success:
        return jsonify({
            "success": True,
            "invitation": result
        })
    else:
        return jsonify({"success": False, "message": message})
    
@app.route('/api/smart-add-shopping-list', methods=['POST'])
def smart_add_shopping_list_route():
    if not check_logged_in():
        return jsonify({"success": False, "message": "You are not logged in."}), 401
    
    data = request.get_json()
    item_name = data.get("item_name", "").strip().capitalize()
    space_id = session.get('current_space_id')
    user_id = session.get('user_id')

    if not space_id or not item_name or len(item_name) > 100:
        return jsonify({"success": False, "message": "Invalid input."}), 400
    
    success, message, new_item_id = database.smart_add_shopping_list(space_id, user_id, item_name)

    if success:
        return jsonify({
            "success": True,
            "item": {
                "list_item_id": new_item_id,
                "product_name": item_name,
                "created_at": datetime.now().strftime("%b %d, %Y")
            }
        })
    else:
        return jsonify({"success": False, "message": message})

if __name__ == '__main__':
    app.run(debug=False, port=8080)