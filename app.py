from flask import Flask, jsonify, request, session
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_mail import Mail, Message

app = Flask(__name__)


CORS(app, resources={r"/*": {"origins": "*"}})

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_DB'] = 'ecommerce'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

app.secret_key = 'aa'

# Route de connexion
@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    mdp = request.json.get('password')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE Email=%s", (email,))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        stored_password = user_data['password']
        print(f"Stored Password: {stored_password}")

        if bcrypt.check_password_hash(stored_password, mdp):
            session['user_id'] = user_data['id']
            return jsonify({'message': 'Login successful', 'user': user_data['id']}), 200
        else:
            return jsonify({'message': 'Invalid email or password'}), 401
    else:
        return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/signup', methods=['POST'])
def signup():
    cur = mysql.connection.cursor()
    data = request.get_json()

    required_fields = ['username', 'email', 'password', 'address']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    email = data.get('email')

    cur.execute("SELECT * FROM users WHERE Email=%s", (email,))
    existing_user = cur.fetchone()

    if existing_user:
        return jsonify({'message': 'User with this email already exists'}), 400

    username = data.get('username')
    address = data.get('address')
    password = data.get('password')  

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    cur.execute("INSERT INTO users (Username, Email, Address, password) VALUES (%s, %s, %s, %s)",
                (username, email, address, hashed_password))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Utilisateur créé avec succès', 'user': cur.lastrowid}), 201

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'amalbouaouina6@gmail.com'  
app.config['MAIL_PASSWORD'] = 'nrzi ldpq cswn yrxf'  

mail = Mail(app)
@app.route('/send_order_email', methods=['POST'])
def send_order_email():
    data = request.json
    user_email = data.get('email')
    user_name = data.get('name')
    products = data.get('products')

    if not user_email or not user_name or not products:
        return jsonify({'message': 'Invalid data'}), 400

    try:
        product_details = "\n".join(
            [f"{p['name']} (Quantité: {p['quantity']})" for p in products]
        )

        msg = Message(
            "Votre commande est prête à être livrée !",
            sender="amalbouaouina6@gmail.com",
            recipients=[user_email],
        )
        msg.body = f"""
Bonjour {user_name},

Votre commande contenant les produits suivants est prête à être livrée :
{product_details}

Merci pour votre confiance !
        """
        mail.send(msg)
        return jsonify({'message': 'Email envoyé avec succès !'}), 200
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")
        return jsonify({'message': 'Erreur lors de l\'envoi de l\'email.'}), 500

@app.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        return jsonify({
            'username': user_data['username'],
            'email': user_data['email'],
            'address': user_data['address'],
        })
    else:
        return jsonify({'message': 'User not found'}), 404
    
@app.route('/profile/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user_data = cur.fetchone()

    if not user_data:
        cur.close()
        return jsonify({'message': 'User not found'}), 404

    if 'username' in data or 'email' in data or 'address' in data:
        updated_username = data.get('username', user_data['username'])
        updated_email = data.get('email', user_data['email'])
        updated_address = data.get('address', user_data['address'])

        query = """
            UPDATE users 
            SET username=%s, email=%s, address=%s
            WHERE id=%s
        """
        values = (updated_username, updated_email, updated_address, user_id)
        cur.execute(query, values)

    if 'current_password' in data and 'new_password' in data:
        current_password = data['current_password']
        new_password = data['new_password']

        stored_password = user_data['password']
        if bcrypt.check_password_hash(stored_password, current_password):
            hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            cur.execute("UPDATE users SET password=%s WHERE id=%s", (hashed_new_password, user_id))
        else:
            cur.close()
            return jsonify({'message': 'Current password is incorrect'}), 400

    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'User updated successfully'}), 200




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
