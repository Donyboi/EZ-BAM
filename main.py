from flask import Flask,render_template,request,redirect,url_for

import pymysql

from dynaconf import Dynaconf

app = Flask(__name__)

config = Dynaconf(settings_file=["setting.toml"])

def connect_db():
    conn = pymysql.connect(
        host="db.steamcenter.tech",
        user="djean2",
        password=config.password,
        database="djean2_ez-bam",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    return conn 

@app.route("/")
def index():
    return render_template("homepage.html.jinja")

@app.route("/browse")
def browse():
    connection = connect_db()
    
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `Product`")

    result = cursor.fetchall()

    connection.close()

    return render_template("browse.html.jinja", products=result)


@app.route("/product/<product_id>")
def product_page(product_id):

    connection =connect_db()

    cursor = connection.cursor()

    cursor.execute( "SELECT * FROM `Product` WHERE `ID` = %s",(product_id))

    result = cursor.fetchone()

    connection.close()

    return render_template("product.html.jinja", product=result)
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "password":
            return redirect(url_for("index"))
    
        else:
            return render_template("login.html.jinja",
                                error= "Invalid username or password")
    return render_template("login.html.jinja")

if __name__ == "_main_":
    app.run(debug=True)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('signup.html.jinja', error='Username and password required')
        
        connection = connect_db()
        cursor = connection.cursor()
        
        cursor.execute("SELECT * FROM `User` WHERE `username` = %s", (username,))
        if cursor.fetchone():
            connection.close()
            return render_template('signup.html.jinja', error='Username already exists')
        
        cursor.execute("INSERT INTO `User` (username, password) VALUES (%s, %s)", (username, password))
        connection.close()
        
        return redirect(url_for('login'))
    
    return render_template('signup.html.jinja')