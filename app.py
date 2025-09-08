from flask import Flask, render_template, redirect, session, request
import database, dotenv, os

try:
    dotenv.load_dotenv()
except Exception as e:
    # Vercel
    print("No .env file found, proceeding with system environment variables.")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.route('/')
def index():
    return render_template('index.html', session=session)

@app.route('/login')
def login():
    return render_template('auth.html', action='login', session=session)

@app.route('/register')
def register():
    return render_template('auth.html', action='register', session=session)

@app.route('/login/submit', methods=['POST'])
def login_submit():
    username = request.form['username']
    password = request.form['password']
    success, message = database.login(username, password)
    if success:
        session['username'] = username
        session['logged_in'] = True
        return redirect('/')
    else:
        return render_template('auth.html', action='login', error=message, session=session)
    
@app.route('/register/submit', methods=['POST'])
def register_submit():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    success, message = database.register(username, password, email)
    if success:
        session['username'] = username
        session['logged_in'] = True
        return redirect('/')
    else:
        return render_template('auth.html', action='register', error=message, session=session)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=8080)