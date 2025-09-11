from flask import Flask, render_template, redirect, session, request
import database, dotenv, os, re
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
    password = request.form['password']
    success, message = database.login(username, password)
    
    # Sanitize username: allow only alphanumeric and underscores, reject others
    if not re.match(r'^\w+$', username):
        return render_template('auth.html', action='login', message='Invalid username: only letters, numbers, and underscores are allowed.', session=session)
    
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
    
    space = database.get_space_details(space_id)
    
    session['current_space_id'] = space_id
    
    # get shopping list
    shopping_list = database.get_shopping_list(space_id)
    for item in shopping_list:
        user_id = item.get('added_by_user_id')
        # Get username from user_id
        item['username'] = database.get_username(user_id)
        
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
    
    return render_template('space.html', session=session, space=space, items=items, shopping_list=shopping_list)

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

@app.route("/api/toggle-shopping-list-item/<item_id>")
def toggle_shopping_list_item(item_id):
    if not check_logged_in():
        return redirect('/login')
    
    success, message = database.toggle_shopping_list_item(item_id)
    
    if success:
        return redirect(f'/space/{session.get("current_space_id")}')
    else:
        return message, 500
    
@app.route("/api/add-to-space-list", methods=['POST'])
def add_item_to_space_list():
    if not check_logged_in():
        return redirect('/login')
    
    item_name = request.form.get('item_name')
    #if item_name:
    #    item_name = item_name.capitalize()

    date = request.form.get('expiration_date')
    # date null in db if not passed through, as its optional
    if not date:
        date = None

    amount = request.form.get('amount')
    unit = request.form.get('unit')
        
    space_id = session.get('current_space_id')
    user_id = session.get('user_id')
    
    if not space_id or not item_name or len(item_name) > 100:
        return "Invalid input.", 400
    
    success, message = database.add_item_to_space_list(space_id, user_id, item_name, date, amount, unit)
    
    if success:
        return redirect(f'/space/{space_id}')
    else:
        return message, 500

@app.route("/api/modify-item-amount/<item_id>", methods=['POST'])
def modify_item_amount(item_id):
    if not check_logged_in():
        return redirect('/login')
    
    amount = request.form.get('amount')
    
    success, message = database.modify_item_amount(item_id, amount)
    
    if success:
        return redirect(f'/space/{session.get("current_space_id")}')
    else:
        return message, 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)