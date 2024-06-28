from flask import Flask, render_template, request, redirect, session
import mysql.connector
from functools import wraps
import os
import smtplib
from dotenv import load_dotenv
import datetime
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '0029')


load_dotenv()
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = os.getenv('SMTP_USERNAME')
smtp_password = os.getenv('SMTP_PASSWORD')

generated_otp = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        try:
            mydb = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Arth@F1',
                database='svadishtam'
            )
            cur = mydb.cursor()
            user = request.form['userid']
            password = request.form['password']

            cur.execute("SELECT * FROM USERS WHERE email = %s AND password = %s AND role='admin'", (user, password))
            data = cur.fetchall()

            if data:
                session['username'] = data[-1][1]
                session['logged_in'] = True
                return redirect('/home')
            else:
                return "Login failed. Please check your user ID and password."

        except mysql.connector.Error as err:
            print("MySQL Error:", err)  
            return f"An error occurred while logging in: {err}"

        finally:
            if 'cur' in locals() and cur:
                cur.close()
            if 'mydb' in locals() and mydb:
                mydb.close()
    return render_template('index.html')


def login_required(f):
    @wraps(f)
    def check_login(*args, **kwargs):
        if 'logged_in' in session and session['logged_in']:
            return f(*args, **kwargs)
        else:
            return redirect('/')

    return check_login

@app.route('/home')
@login_required
def home():
    username = session.get('username')
    return render_template('home.html', username=username)

@app.route('/reset')
def reset():
    return render_template('reset.html')

@app.route('/resetp', methods=['POST'])
def resetp():
    try:
        mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Arth@F1',
            database='svadishtam'
        )
        cur = mydb.cursor()
        newp = request.form['newpass']
        user = request.form['user_id']
        cur.execute('UPDATE USERS SET password=%s WHERE email=%s', (newp, user))
        mydb.commit()
        return redirect('/')

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return "An error occurred"

    finally:
        if cur:
            cur.close()
        if mydb:
            mydb.close()

def send_otp_email(to_email, otp):
    subject = "Your OTP Code"
    body = f"Your OTP code is {otp}"

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        print("Email sent successfully!")
        return True

    except Exception as e:
        print(f"Failed to send email. Error: {e}")
        return False

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        user_id = request.form['userid']
        otp = request.form.get('otp')
        session_otp = session.get('generated_otp')

        if otp:
            if int(otp) == session_otp:
                return redirect('/reset')
            else:
                return "Invalid OTP"
        else:
            generated_otp = random.randint(100000, 999999)
            session['generated_otp'] = generated_otp

            
            send_otp_email(user_id, generated_otp)

            return render_template('forgot.html', otp_sent=True)

    return render_template('forgot.html', otp_sent=False)

@app.route('/success')
def success():
    return "OTP verified successfully!"

@app.route('/sales')
@login_required
def sales():
    if not session.get('logged_in'):
        return redirect('/login')
    username = session.get('username')
    return render_template('sales.html', username=username)

@app.route('/submit', methods=['POST'])
@login_required
def submit_sales():
    if not session.get('logged_in'):
        return redirect('/index')

    try:
        mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Arth@F1',
            database='svadishtam'
        )
        cur = mydb.cursor()

        date = datetime.datetime.strptime(request.form['date'],'%Y-%m-%d')
        day_of_week = date.strftime("%A")

        cash = int(request.form['cash'])
        online = int(request.form['online'])
        card = int(request.form['card'])
        entry_by = request.form['entry_by']

        total = cash + online + card

        cur.execute("SELECT * FROM REVENUES")
        data = cur.fetchall()

        total2 = 0
        if data:
            total2 = data[-1][5]

        data = (date, day_of_week, cash, online, card, total, total - total2, entry_by)
        cur.execute("INSERT INTO REVENUES (date, day, cash, online, card, total, difference_from_yesterday, entry_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", data)
        mydb.commit()

        return redirect('/home')

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return "An error occurred while inserting data"

    finally:
        if cur:
            cur.close()
        if mydb:
            mydb.close()

@app.route('/expense')
@login_required
def expense():
    if not session.get('logged_in'):
        return redirect('/index')
    username = session.get('username')
    return render_template('expense.html', username=username)

@app.route('/submit2', methods=['POST'])
@login_required
def submit_expense():
    if not session.get('logged_in'):
        return redirect('/index')

    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Arth@F1",
            database="svadishtam"
        )
        cur = mydb.cursor()
        
       

        date = datetime.datetime.strptime(request.form['date2'],'%Y-%m-%d')
        day_of_week = date.strftime("%A")
        dry_items = int(request.form['dry_items'])
        di = request.form['di']
        green_groceries = int(request.form['green_groceries'])
        gi = request.form['gi']
        fuel = int(request.form['fuel'])
        fu = request.form['fu']
        staff_convenience = int(request.form['staff_convenience'])
        sc = request.form['sc']
        packaging = int(request.form['packaging'])
        pack = request.form['pack']
        beverages = int(request.form['beverages'])
        bever = request.form['bever']
        extras = int(request.form['extras'])
        ext = request.form['ext']
        expense = dry_items + green_groceries + staff_convenience + packaging + beverages + extras + fuel
        desc = f"Dry items\n{di}\nGreen Groceries\n{gi}\nFuel:\n{fu}\nStaff Convenience\n{sc}\nPackaging:\n{pack}\nBeverages\n{bever}\nExtras\n{ext}"
        data = [date, day_of_week, dry_items, green_groceries, fuel, staff_convenience, packaging, beverages, extras, expense, desc]
        cur.execute("INSERT INTO EXPENSE (date, day, dry_items, green_groceries, fuel, staff_convenience, packaging, beverages, extras, net_expense, description) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", data)
        mydb.commit()
        return redirect('/home')

    except mysql.connector.Error as er:
        print("MySQL Error:", er.msg)
        return "An error occurred while inserting data"

    except KeyError as ke:
        print("KeyError:", ke)
        return "Date field not found in form data"

    finally:
        if cur:
            cur.close()
        if mydb:
            mydb.close()

@app.route('/employees')
@login_required
def employees():
    if not session.get('logged_in'):
        return redirect('/index')
    try:
        mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Arth@F1',
            database='svadishtam'
        )
        cur = mydb.cursor()
        cur.execute("SELECT * FROM employees;")
        table = cur.fetchall()
        return render_template('employees.html', username=session.get('username'), table=table)
    except mysql.connector.Error as err:
        print("MySQL Error:", err)
        return "An error occurred while fetching data"

    finally:
        if cur:
            cur.close()
        if mydb:
            mydb.close()

@app.route('/edit_employee', methods=['POST'])
@login_required
def edit_employee():
    if request.method == 'POST':
        try:
            mydb = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Arth@F1',
                database='svadishtam'
            )
            cur = mydb.cursor()

            employee_id = request.form['employee_id']
            name = request.form['name']
            designation = request.form['designation']
            aadhar = request.form['aadhar']
            salary = request.form['salary']
            email = request.form['email']
            dob = request.form['dob'] if request.form['dob'] != '' else None
            doj = request.form['doj'] if request.form['doj'] !='' else None
            mobile = request.form['mobile']

            cur.execute("UPDATE employees SET name=%s, designation=%s, aadhar=%s, salary=%s, email=%s, dob=%s, doj=%s, mobile=%s WHERE id=%s", (name, designation, aadhar, salary, email, dob, doj, mobile, employee_id))
            mydb.commit()

            return redirect('/employees')

        except mysql.connector.Error as err:
            print(f"MySQL Error: {err.msg}")
            return f"An error occurred while updating employee: {err.msg}"

        finally:
            if cur:
                cur.close()
            if mydb:
                mydb.close()

    return redirect('/')

   
@app.route('/add_employee', methods=['POST'])
@login_required
def add_employee():
    if not session.get('logged_in'):
        return redirect('/index')

    try:
        mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Arth@F1',
            database='svadishtam'
        )
        cur = mydb.cursor()

        name = request.form['name']
        designation = request.form['designation']
        aadhar = request.form['aadhar']
        salary = request.form['salary']
        email = request.form['email']
        dob = request.form['dob']
        if dob == '':
            dob = None   
        doj = request.form['doj']
        if doj=='':
            doj=None
        mobile = request.form['mobile']

        data = (name, designation, aadhar, salary, email, dob, doj, mobile)
        cur.execute("INSERT INTO employees (name, designation, aadhar, salary, email, dob, doj, mobile) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", data)
        mydb.commit()

        return redirect('/employees')  

    except mysql.connector.Error as err:
        error_message = f"An error occurred while adding employee: {err.msg}"
        print(error_message)
        return error_message

    finally:
        if cur:
            cur.close()
        if mydb:
            mydb.close()

@app.route('/profit')
@login_required
def profit():
    try:
        
        mydb = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Arth@F1',
            database='svadishtam'
        )
        cur = mydb.cursor()

        
        cur.execute('SELECT date, net_expense FROM expense')
        expenses = cur.fetchall()

        
        cur.execute('SELECT date, total FROM revenues')
        revenues = cur.fetchall()

       
        expense_dict = {exp[0].strftime('%Y-%m-%d'): exp[1] for exp in expenses}
        revenue_dict = {rev[0].strftime('%Y-%m-%d'): rev[1] for rev in revenues}

        
        daily_data = []
        for date in sorted(set(expense_dict.keys()).union(revenue_dict.keys())):
            net_expense = expense_dict.get(date, 0)
            net_sales = revenue_dict.get(date, 0)
            net_profit = net_sales - net_expense
            daily_data.append((date, net_sales, net_expense, net_profit))

      
        monthly_data = {}
        for date, net_sales, net_expense, net_profit in daily_data:
            month = date[:7]  
            if month not in monthly_data:
                monthly_data[month] = {'sales': 0, 'expenses': 0, 'profits': 0}
            monthly_data[month]['sales'] += net_sales
            monthly_data[month]['expenses'] += net_expense
            monthly_data[month]['profits'] += net_profit

            daily_chart_data = {
                'labels': [data[0] for data in daily_data],
                'sales': [data[1] for data in daily_data],
                'expenses': [data[2] for data in daily_data],
                'profits': [data[3] for data in daily_data]
            }

            monthly_chart_data = {
                'labels': list(monthly_data.keys()),
                'sales': [data['sales'] for data in monthly_data.values()],
                'expenses': [data['expenses'] for data in monthly_data.values()],
                'profits': [data['profits'] for data in monthly_data.values()]
            }

        return render_template('profit.html',username=session.get('username'), daily_chart_data=daily_chart_data, monthly_chart_data=monthly_chart_data)


    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return "An error occurred while fetching data"

    finally:
        if cur:
            cur.close()
        if mydb:
            mydb.close()
@app.route('/customers')
@login_required
def customers():
    if not session.get('logged_in'):
        return redirect('/index')
    try:
        mydb=mysql.connector.connect(
            host='localhost',
            user='root',
            password='Arth@F1',
            database='svadishtam',
        )
        cur=mydb.cursor()
        cur.execute('select * from customers')
        table=cur.fetchall()
        return render_template('customers.html', username=session.get('username'), table=table)
    except mysql.connector.Error as err:
        print("MySQL Error:", err)
        return "An error occurred while fetching data"

    finally:
        if cur:
            cur.close()
        if mydb:
            mydb.close()
@app.route('/add_customer', methods=['POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        try:
            mydb = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Arth@F1',
                database='svadishtam'
            )
            cur = mydb.cursor()

            name = request.form['name']
            email = request.form['email']
            mobile = request.form['mobile']
            address = request.form['address']
            birthdate = request.form['birthdate']
            anniversary = request.form['anniversary']
            
            print(f"Adding customer: {name}, {email}, {mobile}, {address}, {birthdate}, {anniversary}")

            query = "INSERT INTO CUSTOMERS (name, email, mobile, address, birthdate, anniversary) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (name, email, mobile, address, birthdate, anniversary)
            
            cur.execute(query, values)
            mydb.commit()

            print("Customer added successfully")
            return redirect('/customers')
        except Exception as e:
            print(f"Error occurred: {e}")
            return render_template('customers.html', error="Error occurred while adding customer.")
        finally:
            cur.close()
            mydb.close()


@app.route('/edit_customer', methods=['POST'])
@login_required
def edit_customer():
    if request.method == 'POST':
        try:
            mydb = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Arth@F1',
                database='svadishtam'
            )
            cur = mydb.cursor()
            customer_id = request.form['customer_id']
            name = request.form['name']
            email = request.form['email']
            mobile = request.form['mobile']
            address = request.form['address']
            birthdate = request.form['birthdate']
            anniversary = request.form['anniversary']
            
            cur.execute("UPDATE CUSTOMERS SET name=%s, email=%s, mobile=%s, address=%s, birthdate=%s, anniversary=%s WHERE id=%s", 
                        (name, email, mobile, address, birthdate, anniversary, customer_id))
            mydb.commit()
            return redirect('/customers')
        except Exception as e:
            print(e)
            return render_template('customers.html', error="Error occurred while updating customer.")
@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
