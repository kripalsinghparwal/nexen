from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="food_portal"
)

cursor = db.cursor()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_user():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']

    cursor.execute("INSERT INTO users (name,email,phone,password) VALUES (%s,%s,%s,%s)", (name,email,phone,password))
    db.commit()
    return "Registration Successful!"

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_user():
    email = request.form['email']
    password = request.form['password']

    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email,password))
    user = cursor.fetchone()

    if user:
        return "Login Successful!"
    return "Invalid Credentials"

@app.route('/donate')
def donate_page():
    return render_template('donate.html')

@app.route('/donate', methods=['POST'])
def donate_food():
    cursor.execute("INSERT INTO donations (name,food_type,quantity,address,phone) VALUES (%s,%s,%s,%s,%s)",
                   (request.form['name'],request.form['food_type'],request.form['quantity'],request.form['address'],request.form['phone']))
    db.commit()
    return "Food Donated Successfully!"

@app.route('/request')
def request_page():
    return render_template('request.html')

@app.route('/request', methods=['POST'])
def request_food():
    cursor.execute("INSERT INTO requests (name,organization,quantity,address,phone) VALUES (%s,%s,%s,%s,%s)",
                   (request.form['name'],request.form['organization'],request.form['quantity'],request.form['address'],request.form['phone']))
    db.commit()
    return "Request Submitted Successfully!"

@app.route('/admin')
def admin():
    cursor.execute("SELECT * FROM donations")
    donations = cursor.fetchall()

    cursor.execute("SELECT * FROM requests")
    requests = cursor.fetchall()

    return render_template('admin.html', donations=donations, requests=requests)

if __name__ == '__main__':
    app.run(debug=True)
