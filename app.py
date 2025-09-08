from flask import Flask, render_template, redirect, session

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('auth.html', action='login')

@app.route('/register')
def register():
    return render_template('auth.html', action='register')

if __name__ == '__main__':
    app.run(debug=True, port=8080)