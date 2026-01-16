from flask import Flask,render_template,request,redirect,url_for, flash,abort
from flask_login import LoginManager, login_user, login_required, UserMixin, logout_user, current_user

import pymysql

from dynaconf import Dynaconf

app = Flask(__name__)



config = Dynaconf(settings_file=["settings.toml"])

app.secret_key = config.secret_key

login_manager = LoginManager( app )

login_manager.login_view = '/login'

class User:
    is_authenticated = True
    is_active = True
    is_anoonymous = False

    def __init__(self, result):
        self.name = result['Username']
        self.email = result['Email']
        self.address = result['Address']
        self.id = result['ID']
    
    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(" SELECT * FROM `User` WHERE `ID` = %s ", ( user_id ))

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return None
    
    return User(result)

@app.errorhandler(404)
def page_not_found(e):
        return render_template("404.html.jinja"), 404



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


@app.route("/product/<product_id>", methods=["GET"])
@login_required
def product_page(product_id):

    connection =connect_db()

    cursor = connection.cursor()

    cursor.execute( "SELECT * FROM `Product` WHERE `ID` = %s", (product_id))


    result = cursor.fetchone()

    
    if result is None:
        connection.close()
        abort(404)
    

    cursor.execute("""SELECT * FROM `Review` 
                    JOIN `User` ON `Review`.`UserID` = User.ID
                   WHERE `Review`.`ProductID` = %s
                   
            """, (product_id))
    reviews = cursor.fetchall()

    connection.close()




    return render_template("product.html.jinja", product=result, reviews = reviews)


@app.route("/product/<product_id>/add_to_cart", methods=["POST"])
@login_required
def app_to_cart(product_id):

    quantity = request.form["qty:"]

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO `Cart` (`Quantity`, `ProductID`, `UserID`)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
        `Quantity` = `Quantity` + %s
    """, (quantity, product_id, current_user.id, quantity))
    

    flash("Added to Cart")
    return redirect('/browse')



@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        connection =connect_db()

        cursor = connection.cursor()

        cursor.execute("SELECT * FROM  `User` WHERE `email` = %s",(email))

        result = cursor.fetchone()


        connection.close()

        if result is None:
            flash("No User found")
        elif password != result["Password"]:
            flash("Incorrect password")
        else:
            login_user(User (result))
            return redirect ("/browse")

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
            connection = connect_db()
            cursor = connection.cursor()
            try:
                cursor.execute("""
                    INSERT INTO `User` (`Username`, `Email`, `Password`, `Address`)
                    VALUES (%s, %s, %s, %s)
                """, ( username ,email ,password ,address))
                connection.close()
            except pymysql.err.IntegrityError:
                flash("User with that email already exist")
                connection.close()
            else:
                return redirect("/login")
            
    return render_template("signup.html.jinja")        

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("you have been terminated from EZ-BAM :)")
    return redirect('/')
            


            
    


@app.route("/cart")
@login_required
def cart():
        connection = connect_db()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT * FROM `Cart`
            Join `Product` ON `Product`.`ID` = `Cart`.`ProductID`
            WHERE `UserID` = %s             
                    
        """,(current_user.id))

        result = cursor.fetchall()

        total = 0

        for item in result:
            total += item["Price"] * item["Quantity"]

        connection.close()

        return render_template("cart.html.jinja", cart=result, total=total)


@app.route("/cart/<product_id>/update_qty", methods =["POST"])
@login_required
def update_cart(product_id):

        new_qty = request.form["qty"]

        connection = connect_db()

        cursor = connection.cursor()

        cursor.execute("""
            UPDATE `Cart`
            SET `Quantity` = %s
                WHERE `ProductID` = %s AND `UserID` = %s
            """,(new_qty, product_id, current_user.id))
        
        connection.close()

        return redirect("/cart")


@app.route("/cart/<product_id>/remove", methods=['POST'])
@login_required
def remove_from_cart(product_id):

        connection = connect_db()

        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM Cart
            WHERE ProductID = %s AND UserID = %s
    """, (product_id, current_user.id))
        
        connection.close()

        return redirect ("/cart")

@app.route("/checkout", methods =["POST","GET"])
@login_required
def checkout():
        connection = connect_db()

        cursor = connection.cursor()

        cursor.execute("""
            SELECT * FROM `Cart`
            Join `Product` ON `Product`.`ID` = `Cart`.`ProductID`
            WHERE `UserID` = %s             
                    
        """,(current_user.id))

        result = cursor.fetchall()

        if request.method == 'POST':
            
            cursor.execute("INSERT INTO `Sale` (`UserID`) VALUES (%s)", ( current_user.id, ) )
            
            sale = cursor.lastrowid
            for item in result:
                cursor.execute( """
                    INSERT INTO `SaleCart` 
                        (`SaleID`,`ProductID`, `Quantity`)
                    VALUES
                        (%s,%s,%s)
                                
                            
                            """  , (sale, item['ProductID'], item['Quantity']))
            # empty cart
            cursor.execute("DELETE FROM `Cart` WHERE `UserID` = %s", (current_user.id,))
            #thank you screen

            return redirect('/thank-you')       

        total = 0

        for item in result:
            total += item["Price"] * item["Quantity"]

        connection.close()

        return render_template("checkout.html.jinja", cart=result, total=total)


@app.route("/thank-you")
def thankyou():
        return render_template("thankyou.html.jinja")


@app.route("/order")
@login_required
def order():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
             `Sale`.`ID`,
             `Sale`.`Timestamp`,
            SUM(`SaleCart`.Quantity) AS 'Quantity',
            SUM(`SaleCart`.`Quantity` * `Product`.`Price`) AS 'Total'
        FROM `Sale`
        JOIN `SaleCart` ON `SaleCart`.`SaleID` = `Sale`.`ID`
        JOIN `Product` ON `Product`.`ID` = `SaleCart`.`ProductID`
        WHERE `UserID` =%s
        GROUP BY `Sale`.`ID`;
    """,(current_user.id,))

    results = cursor.fetchall()

    connection.close()

    return render_template("order.html.jinja", order=results)


@app.route("/product/<product_id>/review", methods=["POST"])
@login_required
def add_review(product_id):

     
    rating = request.form["rating"]
    comments = request.form["comment"]

    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO  `Review`
            (`Rating`,`Comment`,`ProductID`,`UserID`)
            VALUES
                (%s,%s,%s,%s)                       
                    
        """, (rating, comments, product_id, current_user.id))
    connection.close()

    return redirect(f"/product/{product_id}")