from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_cors import CORS

app = Flask(__name__)


CORS(app, resources={r"/*": {"origins": "*"}})

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_DB'] = 'ecommerce'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

app.secret_key = 'aa'
@app.route('/place_order', methods=['POST'])
def place_order():
    try:
        # Récupération des données envoyées dans la requête
        data = request.json
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        total = data.get('total')
        cart_items = data.get('cart_items', [])

        if not user_id or not total or not cart_items:
            return jsonify({'message': 'Missing user_id, total, or cart_items'}), 400

        # Logs pour vérifier les données reçues
        print(f"Received data: user_id={user_id}, total={total}, cart_items={cart_items}")

        # Connexion et curseur pour la base de données
        cur = mysql.connection.cursor()

        # Commencer une transaction
        cur.execute("START TRANSACTION")
        print("Transaction started...")

        # Insertion dans la table order_summary
        query_summary = "INSERT INTO order_summary (user_id, total) VALUES (%s, %s)"
        cur.execute(query_summary, (user_id, total))
        mysql.connection.commit()  # Validation explicite pour s'assurer de l'insertion

        # Récupération de l'ID de la commande créée
        order_id = cur.lastrowid
        print(f"Inserted into order_summary. Generated order_id: {order_id}")

        # Insertion des articles du panier dans la table cart
        for item in cart_items:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            item_total = item.get('total')

            if not product_id or not quantity or not item_total:
                return jsonify({'message': 'Invalid cart item data'}), 400

            query_cart = """
                INSERT INTO cart (user_id, product_id, quantity, total, order_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(query_cart, (user_id, product_id, quantity, item_total, order_id))
            print(f"Inserted item: {item}")

        # Valider la transaction
        mysql.connection.commit()
        print("Transaction committed successfully.")

        # Fermer le curseur
        cur.close()

        # Retourner une réponse de succès
        return jsonify({'message': 'Order placed successfully', 'order_id': order_id}), 200

    except Exception as e:
        # Annuler la transaction en cas d'erreur
        print(f"Error occurred: {e}")
        mysql.connection.rollback()

        if 'cur' in locals():  # Assurez-vous que le curseur est fermé s'il existe
            cur.close()
        return jsonify({'message': 'Failed to place order', 'error': str(e)}), 500





@app.route('/update_product_quantity', methods=['POST'])
def update_product_quantity():
    try:
        data = request.json
        product_id = data['product_id']
        quantity = data['quantity']

        cur = mysql.connection.cursor()

        query_check = "SELECT stock FROM products WHERE id = %s"
        cur.execute(query_check, (product_id,))
        stock = cur.fetchone()

        stock_quantity = stock['stock'] if isinstance(stock, dict) and 'stock' in stock else stock[0]

        if stock_quantity < quantity:
            return jsonify({'message': 'Stock insuffisant'}), 400

        query = "UPDATE products SET stock = stock - %s WHERE id = %s"
        cur.execute(query, (quantity, product_id))
        mysql.connection.commit()

        cur.close()

        # Ajoutez cette ligne pour retourner une réponse de succès
        return jsonify({'message': 'Stock mis à jour avec succès'}), 200

    except Exception as e:
        # Assurez-vous de fermer le curseur en cas d'erreur
        if 'cur' in locals():
            cur.close()
        return jsonify({'message': 'Erreur lors de la mise à jour du stock', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
