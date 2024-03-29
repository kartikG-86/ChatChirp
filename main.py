import time
from datetime import datetime
from flask import Flask,render_template,request,redirect,url_for,session,jsonify,make_response
from flask_cors import CORS, cross_origin
from flask_bootstrap import Bootstrap5

from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user,login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc,text
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room
from sqlalchemy.exc import IntegrityError
from flask_gravatar import Gravatar
import secrets
import string

# to generate random id
def generate_random_id(length=9):
    characters = string.digits
    random_id = ''.join(secrets.choice(characters) for i in range(length))
    return int(random_id)

app = Flask(__name__ , static_url_path='/static')
app.secret_key = "dsfdskljsdajdsjfh"
Bootstrap5(app)
# CORS(app,resources={r"/api/*": {"origins": "*", "methods": ["POST","GET"]}}, supports_credentials=True)

new_member = False

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI","sqlite:///chatapplication.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(User).where(User.id == user_id)).scalar()

class User(UserMixin,db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    username = db.Column(db.String(100))
    fullname = db.Column(db.String(100))
    bio = db.Column(db.String(1000))
    date = db.Column(db.String(1000))
    servers = relationship("Servers", back_populates="user")
    server_messages = relationship("ServerMessages",back_populates="user")
    notify = relationship("Notifications",back_populates="user")
    friend_chat = relationship("PersonalMessages",back_populates="user")


class Servers(db.Model):
    __tablename__ = "servers"
    id = db.Column(db.Integer, primary_key=True)
    server_name = db.Column(db.String(100), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = relationship("User", back_populates="servers")
    server_messages = relationship("ServerMessages", back_populates="server")  # Correct the property name
    people = relationship("ServerPeople",back_populates="server")

class ServerPeople(db.Model):
    __tablename__ = "serverpeople"
    id = db.Column(db.Integer,primary_key = True)
    person_name = db.Column(db.String(1000))
    server_id = db.Column(db.Integer,db.ForeignKey("servers.id"))
    user_id = db.Column(db.Integer)
    server = relationship("Servers",back_populates="people")

class ServerMessages(db.Model):
    __tablename__ = "serverMessages"
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(10000))
    server_id = db.Column(db.Integer, db.ForeignKey("servers.id"))
    sender_id = db.Column(db.Integer)
    time = db.Column(db.String(1000))
    curr_date = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = relationship("User", back_populates="server_messages")  # Correct the property name
    server = relationship("Servers", back_populates="server_messages")

class PersonalChat(db.Model):
    __tablename__ = "personalChat"
    id = db.Column(db.Integer,primary_key = True)
    user1_id = db.Column(db.Integer)
    user2_id = db.Column(db.Integer)
    messages = relationship("PersonalMessages",back_populates="chat")


class PersonalMessages(db.Model):
    __tablename__ = "personalMessages"
    id = db.Column(db.Integer,primary_key = True)
    message = db.Column(db.String(10000))
    user_id = db.Column(db.Integer,db.ForeignKey("users.id"))
    chat_id = db.Column(db.Integer,db.ForeignKey("personalChat.id"))
    friend_id = db.Column(db.Integer)
    time = db.Column(db.String(1000))
    curr_date = db.Column(db.String(1000))
    user = relationship("User",back_populates='friend_chat')
    chat = relationship("PersonalChat",back_populates="messages")


class Notifications(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    message = db.Column(db.String(1000))
    server_name = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = relationship("User",back_populates="notify")




with app.app_context():
    db.create_all()


# ----------------------------- user image --------------------------------------
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

@app.route('/newuser', methods=["POST", "GET"])
def newUser():

    if request.method == "POST":
        # Handle POST request
        data = request.form
        print(data)
        date_object = datetime.now()

        formatted_date = date_object.strftime("%B %d, %Y")

        check_user = db.session.execute(db.select(User).where(User.email == data.get("email"))).scalar()

        if check_user:
           return jsonify({'success': False, 'message': 'User already exists'})

        else:
            user = User(
                id = generate_random_id(),
                email=data.get("email"),
                username=data.get("username"),
                password=generate_password_hash(data.get("password"), method='pbkdf2:sha256', salt_length=12),
                date = formatted_date
            )
            db.session.add(user)
            db.session.commit()

            login_user(user)

            print("Your User: ",current_user.id)

            print(current_user)
            return redirect(url_for('get_user_details',id=current_user.id))

    # Handle GET request
    return render_template('signup.html')

@app.route('/login', methods=["POST", "GET"])
@cross_origin()
def login():

    if request.method == "POST":
        # Handle POST request
        data = request.form
        print(data)

        check_user = db.session.execute(db.select(User).where(User.email == data.get("email"))).scalar()

        if check_user:
            print(check_user.password)
            if check_password_hash(check_user.password, data.get("password")):

                login_user(check_user)
                return redirect(url_for('get_user_details',id=current_user.id))
            else:
                return render_template('login.html',message="Enter Valid Credentials")
        else:
            return jsonify({'success': False, 'message': "User doesn't exists"})

    # Handle GET request
    return render_template('login.html',message="")

@app.route('/forgotpassword', methods=["POST", "GET"])
def forgotPassword():
    message = ""
    if request.method == "POST":
        data = request.form
        user = db.session.execute(db.select(User).where(User.email == data.get("email"))).scalar()
        if user:
            if not check_password_hash(user.password, data.get("newpassword")):
                user.password = generate_password_hash(data.get("newpassword"), method='pbkdf2:sha256', salt_length=12)
                db.session.commit()
                print(data.get("newpassword"),user.password)
                # db.session.commit()
                message = "Password changed successfully"
            else:
                message = "Your new password should be different from the previous one"
        else:
            message = "Email not found. Please enter a registered email address."
    return render_template('forgotPassword.html', message=message)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/auth')
def auth_page():
    return render_template('auth.html')

@app.route('/')
def main_page():
    return render_template('main_page.html')

@app.route('/servers')
def get_servers():
    server_database = list(db.session.execute(db.select(Servers)).scalars())
    server_database = [{'search_name': '#' + item.server_name,'search_id':item.id} for item in server_database]
    user_database = list(db.session.execute(db.select(User)).scalars())
    user_database = [{'search_name':'@' + item.username,'search_id':item.id} for item in user_database if item.id != current_user.id]
    search_database = server_database + user_database
    print(search_database)
    return jsonify(search_database)

@app.route('/api/channel/<int:id>', methods=['GET',"OPTIONS"])
@cross_origin()
@login_required
def get_user_details(id):
    # Assume you have a function to get the user details from the database
    global new_member
    user_id = current_user.id
    
    print("User id",user_id)
    
    user = db.session.execute(db.select(User).where(User.id == user_id)).scalar()
    if user:
        print(user)
        all_servers = list(db.session.execute(db.select(Servers)).scalars())
        length = len(all_servers)
        past_messages = list(db.session.execute(db.select(ServerMessages)).scalars())
        print(past_messages)
        server_people = list(db.session.execute(db.select(ServerPeople)).scalars())
        server_people = [{'person_name':item.person_name,'serverId':item.server_id} for item in server_people]
        print(server_people)
        notifications = list(db.session.execute(db.select(Notifications).where(Notifications.user_id == current_user.id)).scalars())
        server_created = set(db.session.execute(db.select(Servers).where(Servers.user_id == current_user.id)).scalars())
        server_joined = list(db.session.execute(db.select(ServerPeople).where(ServerPeople.user_id == current_user.id)).scalars())
        server_new_joined = set()
        for item in server_joined:
            for server in all_servers:
                if item.server_id == server.id:
                    server_new_joined.add(server)
        server_joined = server_created.union(server_new_joined)
        friends = db.session.execute(db.select(PersonalChat)).scalars()
        new_friends = []
        for friend in friends:
            if friend.user1_id != current_user.id:
                friend_user = db.session.execute(db.select(User).where(User.id == friend.user1_id)).scalar()
                new_friends.append(friend_user)
            else:
                friend_user = db.session.execute(db.select(User).where(User.id == friend.user2_id)).scalar()
                new_friends.append(friend_user)



        return render_template('user.html',user=user,servers = all_servers,length=length,past_messages=past_messages,server_people=server_people,notifications=notifications, category = "None",friend_user = "None",server_joined=server_joined,new_friends=new_friends)
        
    else:
        return jsonify({'message': 'User not found'}), 404    


@app.route('/edit_profile',methods=["POST","GET"])
def edit_profile():
    user = db.session.execute(db.select(User).where(User.id == current_user.id)).scalar()
    if request.method == "POST":
        data = request.form
        print(data.get('fullname'))
        user.fullname = data.get('fullname')
        user.username = data.get('username')
        user.email = data.get('email')
        user.bio = data.get('bio')
        db.session.commit()
        return redirect(url_for('get_user_details',id = current_user.id))
    return render_template('edit_profile.html',user=user)


# ---------------------------------------- Create server ------------------------------- 

socketio = SocketIO(app)

servers = {}

@app.route('/server')
def new_server_create():
    return render_template('server.html')

@app.route('/refresh')
def refresh_page():
    # Perform some action or logic here

    # Redirect the client to the same page or another page
    return redirect(url_for('get_user_details'))

@app.route('/api/friend/<int:id>')
@login_required
def friends_chat(id):
    print(id)
    user_id = current_user.id

    user = db.session.execute(db.select(User).where(User.id == user_id)).scalar()
    if user:
        print(user)

        check_personal_chat = db.session.execute(db.select(PersonalChat).where((PersonalChat.user1_id == current_user.id and PersonalChat.user2_id == id))).scalar()
        if not check_personal_chat:
            check_personal_chat = db.session.execute(db.select(PersonalChat).where(PersonalChat.user1_id == id and PersonalChat.user2_id == current_user.id)).scalar()
        print("Personal Chat",check_personal_chat)

        if not check_personal_chat:

            check_personal_chat = PersonalChat(
                id = generate_random_id(),
                user1_id = current_user.id,
                user2_id = id
            )
            db.session.add(check_personal_chat)
            db.session.commit()

        all_servers = list(db.session.execute(db.select(Servers)).scalars())
        length = len(all_servers)
        past_messages = list(db.session.execute(db.select(PersonalMessages).where(PersonalMessages.chat_id == check_personal_chat.id)).scalars())
        print(past_messages)
        notifications = list(db.session.execute(db.select(Notifications).where(Notifications.user_id == current_user.id)).scalars())
        server_created = set(db.session.execute(db.select(Servers).where(Servers.user_id == current_user.id)).scalars())
        server_joined = list(db.session.execute(db.select(ServerPeople).where(ServerPeople.user_id == current_user.id)).scalars())
        server_new_joined = set()
        for item in server_joined:
            for server in all_servers:
                if item.server_id == server.id:
                    server_new_joined.add(server)
        server_joined = server_created.union(server_new_joined)
        friends = db.session.execute(db.select(PersonalChat)).scalars()
        new_friends = []
        for friend in friends:
            if friend.user1_id != current_user.id:
                friend_user = db.session.execute(db.select(User).where(User.id == friend.user1_id)).scalar()
                new_friends.append(friend_user)
            else:
                friend_user = db.session.execute(db.select(User).where(User.id == friend.user2_id)).scalar()
                new_friends.append(friend_user)
        friend_user = db.session.execute(db.select(User).where(User.id == id)).scalar()


        return render_template('user.html',user=user,servers = all_servers,length=length,past_messages=past_messages,notifications=notifications,search_id = id,friend_user=friend_user,category="Personal",personal_chat=check_personal_chat,server_joined=server_joined,new_friends=new_friends)

    return jsonify({'message': 'User not found'}), 404



@app.route('/api/server/<int:id>')
def server_open(id):
    print(id)
    user_id = current_user.id

    print("User id",user_id)

    user = db.session.execute(db.select(User).where(User.id == user_id)).scalar()
    if user:
        print(user)
        user_open_server = db.session.execute(db.select(Servers).where(Servers.id == id)).scalar()

        past_messages = list(db.session.execute(db.select(ServerMessages).where(ServerMessages.server_id == id)).scalars())
        print(past_messages)
        server_people = list(db.session.execute(db.select(ServerPeople).where(ServerPeople.server_id == id)).scalars())
        server_people = [{'person_name':item.person_name,'serverId':item.server_id} for item in server_people]
        print(server_people)
        notifications = list(db.session.execute(db.select(Notifications).where(Notifications.user_id == current_user.id)).scalars())
        all_servers = list(db.session.execute(db.select(Servers)).scalars())
        length = len(all_servers)
        server_created = set(db.session.execute(db.select(Servers).where(Servers.user_id == current_user.id)).scalars())
        server_joined = list(db.session.execute(db.select(ServerPeople).where(ServerPeople.user_id == current_user.id)).scalars())
        server_new_joined = set()
        for item in server_joined:
            for server in all_servers:
                if item.server_id == server.id:
                    server_new_joined.add(server)
        server_joined = server_created.union(server_new_joined)
        friends = db.session.execute(db.select(PersonalChat)).scalars()
        new_friends = []
        for friend in friends:
            if friend.user1_id != current_user.id:
                friend_user = db.session.execute(db.select(User).where(User.id == friend.user1_id)).scalar()
                new_friends.append(friend_user)
            else:
                friend_user = db.session.execute(db.select(User).where(User.id == friend.user2_id)).scalar()
                new_friends.append(friend_user)
        check_server = db.session.execute(db.select(Servers).where(Servers.id == id)).scalar()
        if check_server:
            return render_template('user.html',user=user, servers=all_servers ,user_open_server = user_open_server,length=length,past_messages=past_messages,server_people=server_people,notifications=notifications,search_id = id,category="Server",friend_user = "None",server_joined=server_joined,new_friends=new_friends)
        else:
            return redirect(url_for('friends_chat',id=id))


    return jsonify({'message': 'User not found'}), 404


@socketio.on('create_server')
def create_server(server_name):
    # Check if a server with the given name already exists
    existing_server = Servers.query.filter_by(server_name=server_name).first()
    if existing_server:
        # Emit an error message to the client
        emit('server_created', {'error': True, 'message': 'Server name already exists'}, broadcast=False)
    else:
        try:
            # Create a new server and store it in the database
            new_server = Servers(
                id = generate_random_id(),
                server_name=server_name,
                user_id=current_user.id
            )
            db.session.add(new_server)
            db.session.commit()
            print(f'Server {server_name} created')
            print(new_server)

            user = db.session.execute(db.select(User).where(User.id == current_user.id)).scalar()
            server_people = ServerPeople(
                id = generate_random_id(),
                person_name = user.username,
                server_id = new_server.id,
                user_id = current_user.id
            )
            db.session.add(server_people)
            db.session.commit()

            new_notification = Notifications(
                    message = f"Congratulations {user.username}! You have successfully created this server.",
                    user_id=current_user.id,
                    server_name = server_name
                )
            db.session.add(new_notification)
            db.session.commit()

            # Emit success message to the client
            emit('server_created', {'error': False, 'message': 'Server created successfully','url': url_for('server_open',id=new_server.id )}, broadcast=False)

        except IntegrityError:
            # Handle any integrity errors that may occur during database insertion
            db.session.rollback()
            # Emit an error message to the client
            emit('server_created', {'error': True, 'message': 'An error occurred while creating the server'}, broadcast=False)


@socketio.on('join_server')
def join_server(data):
    username = data['username']
    serverId = data['serverId']
    server = db.session.execute(db.select(Servers).where(Servers.id == serverId)).scalar()
    join_room(server.server_name)
    server_people = ServerPeople(
            id = generate_random_id(),
            person_name = username,
            server_id = serverId,
            user_id = current_user.id
            )
    db.session.add(server_people)
    db.session.commit()

    todayDate = datetime.now().strftime("%B %d, %Y")
    current_time = datetime.now().strftime("%H:%M")
    user = db.session.execute(db.select(User).where(User.id == current_user.id)).scalar()
    message = ServerMessages(
        message='Joined',
        server_id = serverId,
        sender_id = user.id,
        curr_date = todayDate,
        time=current_time,
        user_id = user.id,
    )
    db.session.add(message)
    db.session.commit()
    # server_people = list(db.session.execute(db.select(ServerPeople)).scalars())

    emit('message', {'chatId': serverId, 'message': "Joined",'senderId': user.id,'time':current_time,'username': user.username,'curr_date':todayDate},broadcast=True)  # Emit message to specific server room
    print(f'{username} joined server {serverId} {server.server_name}')

    new_notification = Notifications(

        message = f"Welcome {username}! You have been added to this server.",
        user_id=current_user.id,
        server_name = server.server_name
    )
    db.session.add(new_notification)
    db.session.commit()

    emit('redirect', {'url': url_for('server_open',id=serverId)})

@socketio.on('send_message')
def send_message(data):
    chat_id = data['chatId']
    message = data['message']
    sender_id = data["senderId"]
    print(sender_id)
    todayDate = datetime.now().strftime("%B %d, %Y")
    current_time = datetime.now().strftime("%H:%M")
    check_server = db.session.execute(db.select(Servers).where(Servers.id == chat_id)).scalar()


    if check_server:
        user_message = ServerMessages(
            message=message,
            server_id = chat_id,
            sender_id = sender_id,
            curr_date = todayDate,
            time=current_time,
            user_id = sender_id,
        )

        db.session.add(user_message)
        db.session.commit()
        emit('message', {'chatId': chat_id, 'message': message,'senderId': sender_id,'time':current_time,'username': user_message.user.username,'curr_date':todayDate,'friendId':"None"},broadcast=True)
    else:
        print(chat_id)
        personal_chat = db.session.execute(db.select(PersonalChat).where(PersonalChat.id == chat_id)).scalar()
        print(personal_chat)
        personal_message = PersonalMessages(
            chat_id = chat_id,
            message=message,
            user_id = sender_id if personal_chat.user1_id == sender_id else personal_chat.user2_id,
            friend_id = personal_chat.user2_id if personal_chat.user1_id == sender_id else personal_chat.user1_id ,
            time=current_time,
            curr_date = todayDate,
        )
        db.session.add(personal_message)
        db.session.commit()
        emit('message', {'chatId': chat_id, 'message': message,'senderId': sender_id,'time':current_time,'username': personal_message.user.username,'curr_date':todayDate},broadcast=True)

      # Emit message to specific server room


if __name__ == "__main__":
   
    # app.run(debug=True)
    socketio.run(app,allow_unsafe_werkzeug=True,debug=True)
    # , host="0.0.0.0", port="8080"