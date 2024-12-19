from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask import send_from_directory


app = Flask(__name__)


CORS(app, resources={r"/*": {"origins": "*"}})

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_DB'] = 'ecommerce'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

app.secret_key = 'aa'

@app.route('/products', methods=['GET'])
def get_products():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products')
    products = cur.fetchall()
    cur.close()

    product_list = []
    for product in products:
        product_list.append({
            'id': product['id'],
            'name': product['name'],
            'description': product['description'],
            'price': product['price'],
            'stock': product['stock'],
        })

    return jsonify({'products': product_list})

app.config['UPLOAD_FOLDER'] = 'E:/FLUTTER_PROJECT/VALIDATION/backend/imagesProduit'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/imagesProduit/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



@app.route('/orders/search', methods=['GET'])
def search_orders():
    name = request.args.get('name', '')  # Recherche par nom
    created_at = request.args.get('created_at', None)  # Recherche par date
    cur = mysql.connection.cursor()

    # Construire la requête SQL en fonction des paramètres
    if created_at:
        query = """
        SELECT * FROM order_summary 
        WHERE user_id LIKE %s AND DATE(created_at) = %s
        """
        cur.execute(query, ('%' + name + '%', created_at))
    else:
        query = """
        SELECT * FROM order_summary 
        WHERE user_id LIKE %s
        """
        cur.execute(query, ('%' + name + '%',))

    orders = cur.fetchall()
    cur.close()

    # Transformer les résultats en JSON
    order_list = []
    for order in orders:
        order_list.append({
            'id': order['id'],
            'user_id': order['user_id'],
            'total': order['total'],
            'created_at': order['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
        })

    return jsonify({'orders': order_list})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
