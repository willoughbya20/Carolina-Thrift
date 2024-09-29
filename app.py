from flask import Flask, jsonify,request, render_template, session
from flask_restful import Api, Resource
from werkzeug.utils import secure_filename
import sqlite3, os



def get_db_connection():
    return sqlite3.connect('Carolina_thrift_database.db', check_same_thread=False)

def initialize_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
            Email TEXT PRIMARY KEY, -- PK
            FirstName TEXT,
            LastName TEXT,
            Bio TEXT,
            Password TEXT,
            ProfilePicture BLOB -- Binary large Object
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS UserListings (
            Email TEXT PRIMARY KEY,  -- PK & FK
            Photo BLOB,           -- BLOB for storing listing photos
            Quality TEXT,
            Description TEXT,
            AskingPrice REAL,
            Type TEXT,
            FOREIGN KEY (Email) REFERENCES Users(Email)
        )''')

app = Flask(__name__)
api = Api(app)
initialize_db()
app.secret_key = 'wenagadeWaider'

def query_listings():
    listings = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM UserListings")
            columns = [column[0] for column in cursor.description]
            listings = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
    except Exception as e:
        print(f"Error querying listings: {e}")
    return listings

def create_user(first_name, last_name, email, password, bio=None, profile_picture=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (FirstName, LastName, Email, Bio, Password, ProfilePicture) VALUES (?, ?, ?, ?, ?, ?)",
                   (first_name, last_name, email, bio, password, profile_picture))
        user_id = cursor.lastrowid
        conn.commit()
    return user_id  # Return the ID of the newly created customer

def read_user(email):
    conn = get_db_connection()  # Open the connection
    cursor = conn.cursor()
    cursor.execute("SELECT Email, FirstName, LastName, Bio, ProfilePicture FROM Users WHERE Email=?", (email,))
    user = cursor.fetchone()
    conn.close()  # Close the connection
    return user


def update_user(first_name, last_name, email, bio, password, profile_picture):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        print("Executing SQL statement...")
        # Use ? placeholders for SQLite
        try: 
            cursor.execute(
                "UPDATE Users SET FirstName=?, LastName=?, Email=?, Bio=?, ProfilePicture=? WHERE email=?",
                (first_name, last_name, email, bio, profile_picture, email)
            )
        except Exception as e:
            print(f"Error executing SQL statement: {e}")

        # Commit the transaction
        conn.commit()

        print("Transaction committed successfully.")
        
def delete_user(email):
     with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Users WHERE UserID=?", (email,))
        conn.commit()

def create_listing(email, photo, quality, description, asking_price):
     with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO UserListings (Email, Photo, Quality, Description, AskingPrice) VALUES (?, ?, ?, ?, ?)",
                   (email, photo, quality, description, asking_price))
        conn.commit()
        return cursor.lastrowid  # Return the ID of the newly created listing

def read_listing(email):
     with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM UserListings WHERE Email=?", (email,))
        return cursor.fetchone()  # Returns a single listing as a tuple

def update_listing(email, photo, quality, description, asking_price, listing_type):
     with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE UserListings SET Photo=?, Quality=?, Description=?, AskingPrice=?, Type=? WHERE Email=?",
                   (photo, quality, description, asking_price, listing_type, email))
        conn.commit()

def delete_listing(email):
     with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM UserListings WHERE Email=?", (email,))
        conn.commit()

def create_message(sender_id, receiver_id, message_text):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Messages (SenderID, ReceiverID, MessageText) VALUES (?, ?, ?)",
                   (sender_id, receiver_id, message_text))
        message_id = cursor.lastrowid
        conn.commit()
    return message_id  # Return the ID of the newly created message

def read_message(message_id):
     with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Messages WHERE MessageID=?", (message_id,))
        return cursor.fetchone()  # Returns a single message as a tuple

def update_message(message_id, message_text):
     with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Messages SET MessageText=? WHERE MessageID=?", (message_text, message_id))
        conn.commit()

def delete_message(message_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Messages WHERE MessageID=?", (message_id,))
        conn.commit()

def check_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE Email=? AND Password=?", (email, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user is not None

class UserResource(Resource):
    def get(self, user_id):
        user = read_user(user_id)
        if user:
            # Convert the user tuple to a dictionary for a JSON response
            email, first_name, last_name, bio, password, profile_picture = user
            user_data = {
                "Email": email,
                "FirstName": first_name,
                "LastName": last_name,
                "Bio": bio,
                "Password": password,
                "ProfilePicture": profile_picture
            }
            return user_data, 200
        else:
            return {"message": "User not found"}, 404

    def post(self):
        data = request.get_json()
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        bio = data.get("bio")
        password = data.get("password")
        profile_picture = data.get("profile_picture")

        if not first_name or not last_name or not email:
            return {"message": "Missing required data in the request body"}, 400

        user_id = create_user(first_name, last_name, email, password , bio, profile_picture)

        return {"message": "User created", "user_id": user_id}, 201

    def put(self, user_id):
        data = request.get_json()
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        bio = data.get("bio")
        password = data.get("password")
        profile_picture = data.get("profile_picture")

        if not first_name and not last_name and not email:
            return {"message": "No data provided for update"}, 400

        existing_user = read_user(user_id)
        if not existing_user:
            return {"message": "User not found"}, 404

        update_user(first_name, last_name, email, bio, password, profile_picture)

        return {"message": "User updated"}, 200

    def delete(self, user_id):
        existing_user = read_user(user_id)
        if not existing_user:
            return {"message": "User not found"}, 404

        # Delete the user from the database
        delete_user(user_id)

        return {"message": "User deleted"}, 204

class ListingResource(Resource):
    def get(self, listing_id):
        listing = read_listing(listing_id)
        if listing:
            # Convert the listing tuple to a dictionary for a JSON response
            listing_id, user_id, photo, quality, description, asking_price, listing_type = listing
            listing_data = {
                "ListingID": listing_id,
                "UserID": user_id,
                "Photo": photo,
                "Quality": quality,
                "Description": description,
                "AskingPrice": asking_price,
                "Type": listing_type
            }
            return listing_data, 200
        else:
            return {"message": "Listing not found"}, 404

    def post(self):
        data = request.get_json()
        user_id = data.get("user_id")
        photo = data.get("photo")
        quality = data.get("quality")
        description = data.get("description")
        asking_price = data.get("asking_price")
        listing_type = data.get("listing_type")

        if not user_id or not photo or not quality or not description or not asking_price:
            return {"message": "Missing required data in the request body"}, 400

        listing_id = create_listing(user_id, photo, quality, description, asking_price)

        return {"message": "Listing created", "listing_id": listing_id}, 201

    def put(self, listing_id):
        data = request.get_json()
        photo = data.get("photo")
        quality = data.get("quality")
        description = data.get("description")
        asking_price = data.get("asking_price")
        listing_type = data.get("listing_type")

        if not photo and not quality and not description and not asking_price and not listing_type:
            return {"message": "No data provided for update"}, 400

        existing_listing = read_listing(listing_id)
        if not existing_listing:
            return {"message": "Listing not found"}, 404

        update_listing(listing_id, photo, quality, description, asking_price, listing_type)

        return {"message": "Listing updated"}, 200

    def delete(self, listing_id):
        existing_listing = read_listing(listing_id)
        if not existing_listing:
            return {"message": "Listing not found"}, 404

        # Delete the listing from the database
        delete_listing(listing_id)

        return {"message": "Listing deleted"}, 204

class MessageResource(Resource):
    def get(self, message_id):
        message = read_message(message_id)
        if message:
            # Convert the message tuple to a dictionary for a JSON response
            message_id, sender_id, receiver_id, message_text, timestamp = message
            message_data = {
                "MessageID": message_id,
                "SenderID": sender_id,
                "ReceiverID": receiver_id,
                "MessageText": message_text,
                "Timestamp": timestamp
            }
            return message_data, 200
        else:
            return {"message": "Message not found"}, 404

    def post(self):
        data = request.get_json()
        sender_id = data.get("sender_id")
        receiver_id = data.get("receiver_id")
        message_text = data.get("message_text")

        if not sender_id or not receiver_id or not message_text:
            return {"message": "Missing required data in the request body"}, 400

        message_id = create_message(sender_id, receiver_id, message_text)

        return {"message": "Message created", "message_id": message_id}, 201

    def put(self, message_id):
        data = request.get_json()
        message_text = data.get("message_text")

        if not message_text:
            return {"message": "No data provided for update"}, 400

        existing_message = read_message(message_id)
        if not existing_message:
            return {"message": "Message not found"}, 404

        update_message(message_id, message_text)

        return {"message": "Message updated"}, 200

    def delete(self, message_id):
        existing_message = read_message(message_id)
        if not existing_message:
            return {"message": "Message not found"}, 404

        delete_message(message_id)

        return {"message": "Message deleted"}, 204



api.add_resource(UserResource, '/users', '/users/<int:user_id>')
api.add_resource(ListingResource, '/listings', '/listings/<int:listing_id>')
api.add_resource(MessageResource, '/messages', '/messages/<int:message_id>')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/shop")
def shop():
    products = query_listings()
    for product in products:
        product['Photo'] = base64.b64encode(product['Photo']).decode('utf-8')
    return render_template('shop.html', products=products)

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/contact")
def contact():
    return render_template('contact.html')

@app.route("/dashboard", methods=['GET'])
def dashboard():
    return render_template('dashboard.html')
    
@app.route('/dashboard', methods=['PUT'])
def update_profile():
    user_id = request.form.get('user_id')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    bio = request.form.get('bio')
    password = request.form.get('password')  

    profile_picture = request.files.get('profile_picture')
    profile_picture_data = None
    if profile_picture:
        # Read the file's binary content
        profile_picture_data = profile_picture.read()
    
    try: 
        update_user(first_name, last_name, email, bio, password, profile_picture_data)
    except Exception as e:
        print(f'Error updating user: {e}')

    return jsonify({'message': 'Profile updated successfully'}), 200

@app.route("/dashboard", methods=['POST'])
def create_listing_route():
    print("Form data:", request.form)
    print("Files:", request.files)

    user_email = session.get('email')
    if not user_email:
        return jsonify({"message": "User not logged in"}), 401
    
    quality = request.form.get("quality")
    description = request.form.get("description")
    asking_price = request.form.get("asking-price") 

    photo = request.files.get('photo')
    photo_data = None
    if photo:
        photo_data = photo.read()

    if not quality or not description or not asking_price:
        return jsonify({"message": "Missing required data in the request body"}), 400
    
    try:
        listing_id = create_listing(user_email, photo_data, quality, description, asking_price)
        return jsonify({"message": "Listing created", "listing_id": listing_id}), 201
    except Exception as e:
        print(f'Error creating listing: {e}')
        return jsonify({"message": "Error creating listing"}), 500
    

import base64

@app.route('/get-user-profile', methods=['GET'])
def get_user_profile():
    user_email = session.get('email')
    if not user_email:
        return jsonify({"message": "User not logged in"}), 401

    user_data = read_user(user_email)
    if user_data:
        # Convert the binary data for the profile picture to a Base64-encoded string
        profile_picture_data = user_data[4] if user_data[4] else None
        if profile_picture_data:
            profile_picture_data = base64.b64encode(profile_picture_data).decode('utf-8')

        user_dict = {
            'email': user_data[0],
            'first_name': user_data[1],
            'last_name': user_data[2],
            'bio': user_data[3],
            'profile_picture': profile_picture_data  
        }
        return jsonify(user_dict), 200
    else:
        return jsonify({"message": "User not found"}), 404



    

@app.route("/privacy")
def privacy():
    return render_template('privacy.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([first_name, last_name, email, password]):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
    
    if not email.endswith('ecu.edu'):
        return jsonify({'status': 'error', 'message': 'Invalid email domain. Please use your ECU email.'}), 400

    user_id = create_user(first_name, last_name, email, password)
    if user_id:
        return jsonify({'status': 'success', 'message': 'Registration successful.', 'user_id': user_id}), 200
    else:
        return jsonify({'status': 'error', 'message': 'User already exists or other database error.'}), 400
@app.route('/register', methods=['GET'])
def show_register_form():
    return render_template('register.html')



@app.route("/terms")
def terms():
    return render_template('terms.html')

@app.route('/login', methods=['POST'])
def login():
  
    if not request.is_json:
        return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Error handling for missing email or password
    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
    if check_user(email, password):
        session['logged_in'] = True
        session['email'] = email  # Log the user's email in the session
        return jsonify({'status': 'success','message': 'USERLOGGED'}), 200
    else:
        session['logged_in'] = False
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401


@app.route("/login", methods=['GET'])
def show_login_form():
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)  # Remove the 'logged_in' flag from session
    session.pop('email', None)      # Remove the user's email from session
    return jsonify({'status': 'success', 'message': 'Logged out'}), 200

@app.route('/some_protected_route')
def protected():
    if session.get('logged_in'):
        # User is logged in, proceed with the route
        pass
    else:
        # User is not logged in, redirect to login form or return an error
        pass


if __name__ == '__main__':
    app.run(debug=False)

