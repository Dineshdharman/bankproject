from flask import Flask, session, render_template, redirect, request, url_for
import mysql.connector

app = Flask(__name__)

def get_db_cursor():
    con = mysql.connector.connect(host="localhost", user="root", password="Your password", database="bank")
    cursor = con.cursor(buffered=True)
    return con, cursor

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('choice'))
    return render_template('blogin.html')

@app.route('/choice')
def choice():
    if 'username' not in session:
        return redirect('/')
    return render_template("choice1.html")

@app.route('/account_choice', methods=['POST'])
def account_choice():
    if 'username' not in session:
        return redirect('/')
    account_type = request.form.get('account_type')
    if account_type:
        session['account_type'] = account_type
        return redirect(url_for('choice_redirect'))
    return redirect(url_for('choice'))

@app.route('/choice_redirect')
def choice_redirect():
    if 'username' not in session or 'account_type' not in session:
        return redirect('/')
    username = session['username']
    account_type = session['account_type']
    con, cursor = get_db_cursor()
    table_name = 'bankdetails' if account_type == 'savings' else 'curbankdetails'
    cursor.execute(f'SELECT * FROM {table_name} WHERE Username=%s', (username,))
    user_account = cursor.fetchone()
    cursor.close()
    con.close()
    if user_account:
        return redirect(url_for(f'{account_type}_dashboard'))
    else:
        return render_template("choice1.html", message=f"You do not have an account in {account_type}.")

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    phone = request.form['phone']
    con, cursor = get_db_cursor()
    cursor.execute('SELECT * FROM userdetails WHERE username=%s AND password=%s AND phone=%s', (username, password, phone))
    user = cursor.fetchone()
    cursor.close()
    con.close()
    if user:
        session['username'] = username
        session['phone'] = phone
        return redirect(url_for('choice'))
    else:
        return render_template('blogin.html', message='Invalid username, password or phone number')

@app.route('/savings_dashboard')
def savings_dashboard():
    if 'username' not in session or 'account_type' not in session:
        return redirect('/')
    con, cursor = get_db_cursor()
    cursor.execute('SELECT AccNo, Username, Amount FROM bankdetails WHERE Username=%s', (session['username'],))
    res = cursor.fetchall()
    cursor.close()
    con.close()
    return render_template('savings_dashboard.html', username=session['username'], datas=res)

@app.route('/current_dashboard')
def current_dashboard():
    if 'username' not in session or 'account_type' not in session:
        return redirect('/')
    con, cursor = get_db_cursor()
    cursor.execute('SELECT AccNo, Username, Amount FROM curbankdetails WHERE Username=%s', (session['username'],))
    res = cursor.fetchall()
    cursor.close()
    con.close()
    return render_template('current_dashboard.html', username=session['username'], datas=res)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        account_type = request.args.get('account_type')
        if account_type in ['savings', 'current']:
            session['account_type'] = account_type
            return render_template("signup.html")
        return render_template("choice.html")
    elif request.method == 'POST':
        accno = request.form['AccNo']
        name = request.form['Name']
        amount = request.form['Amount']
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        account_type = session.get('account_type')
        con, cursor = get_db_cursor()
        if account_type == 'savings':
            cursor.execute('INSERT INTO bankdetails(AccNo, Username, Amount) VALUES (%s, %s, %s)', (accno, name, amount))
        elif account_type == 'current':
            cursor.execute('INSERT INTO curbankdetails(AccNo, Username, Amount) VALUES (%s, %s, %s)', (accno, name, amount))
        else:
            return "Invalid account type"
        cursor.execute('INSERT INTO userdetails(username, password, phone) VALUES (%s, %s, %s)', (username, password, phone))
        con.commit()
        cursor.close()
        con.close()
        return redirect('/')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('phone', None)
    session.pop('account_type', None)
    return redirect('/')

@app.route("/withdraw/<string:id>", methods=['GET', 'POST'])
def withdraw(id):
    if 'username' not in session or 'account_type' not in session:
        return redirect('/')
    return_url = request.args.get('return_url', '/')
    con, cursor = get_db_cursor()
    account_type = session['account_type']
    table_name = 'bankdetails' if account_type == 'savings' else 'curbankdetails'
    if request.method == 'POST':
        amount = float(request.form['Amount'])
        cursor.execute(f'SELECT AccNo, Username, Amount FROM {table_name} WHERE AccNo=%s AND Username=%s', (id, session['username']))
        res = cursor.fetchone()
        if res:
            current_balance = float(res[2])
            if current_balance >= amount:
                new_balance = current_balance - amount
                cursor.execute(f'UPDATE {table_name} SET Amount=%s WHERE AccNo=%s', (new_balance, id))
                con.commit()
                cursor.close()
                con.close()
                return render_template("withdraw.html", message=f"You have withdrawn the amount of {amount}", return_url=return_url)
            return render_template("withdraw.html", message="Insufficient Balance", return_url=return_url)
        return render_template("withdraw.html", message="Invalid Account Number", return_url=return_url)
    cursor.execute(f'SELECT AccNo, Username, Amount FROM {table_name} WHERE AccNo=%s AND Username=%s', (id, session['username']))
    res = cursor.fetchone()
    cursor.close()
    con.close()
    return render_template("withdraw.html", datas=res, return_url=return_url)

@app.route("/credit/<string:id>", methods=['GET', 'POST'])
def credit(id):
    if 'username' not in session or 'account_type' not in session:
        return redirect('/')
    return_url = request.args.get('return_url', '/')
    con, cursor = get_db_cursor()
    account_type = session['account_type']
    table_name = 'bankdetails' if account_type == 'savings' else 'curbankdetails'
    if request.method == 'POST':
        amount = float(request.form['Amount'])
        cursor.execute(f'SELECT AccNo, Username, Amount FROM {table_name} WHERE AccNo=%s AND Username=%s', (id, session['username']))
        res = cursor.fetchone()
        if res:
            current_balance = float(res[2])
            if current_balance + amount <= 100000000:
                new_balance = current_balance + amount
                cursor.execute(f'UPDATE {table_name} SET Amount=%s WHERE AccNo=%s', (new_balance, id))
                con.commit()
                cursor.close()
                con.close()
                return render_template("credit.html", message=f"You have credited the amount of {amount}", return_url=return_url)
            return render_template("credit.html", message="You have reached the limit", return_url=return_url)
        return render_template("credit.html", message="Invalid Account Number", return_url=return_url)
    cursor.execute(f"SELECT AccNo, Username, Amount FROM {table_name} WHERE AccNo=%s AND Username=%s", (id, session['username']))
    res = cursor.fetchone()
    cursor.close()
    con.close()
    return render_template("credit.html", datas=res, return_url=return_url)

if __name__ == '__main__':
    app.secret_key = '12345'
    app.run(debug=True)
