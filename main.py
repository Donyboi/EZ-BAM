from flask import Flask,render_template,request,redirect,url_for, flash

import pymysql

from dynaconf import Dynaconf

app = Flask(__name__)



config = Dynaconf(settings_file=["setting.toml"])

app.secret_key = config.secret_key

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
        username = request.form["username"]

        email = request.form["email"]

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        address = request.form["address"]

        if password != confirm_password:
            flash("PASSWORDS DO NOT MATCH >:(")
        elif len(password) < 8:
            flash("Password is to Short")
        else:
            connect_db

            connection = connect_db()
    
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO `User` (`Username, `Password`, `Email`, Address`)
                VALUES (%s, %s, %s, %s)
            """, ( username ,password ,email ,address))

            return redirect('/login')
            
            

    return render_template("signup.html.jinja")