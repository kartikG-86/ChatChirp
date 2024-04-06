# Chatchirp
Chatchirp is a web application developed using Python Flask that allows users to chat with each other either through personal messages or by creating servers for group chats. Users can sign up, log in, edit their profiles, and engage in conversations with other users.

## Features
### User Authentication:

Users can sign up with a unique username and password.
Existing users can log in securely using their credentials.
Passwords are securely hashed and stored in the database.
### Profile Management:

Users can edit their profiles, including changing their username, email, and profile picture.
### Messaging:

Users can send personal messages to other users.
Users can create servers and invite others to join for group chats.
Messages are delivered in real-time using WebSocket communication for a seamless chatting experience.
### Security:

CSRF protection is implemented to prevent Cross-Site Request Forgery attacks.
Passwords are securely hashed using strong encryption algorithms.
Input validation is enforced to prevent injection attacks and ensure data integrity.
## Technologies Used
### Python Flask: Backend web framework for building the application logic and handling HTTP requests.
### SQLite: Lightweight relational database used for storing user data, messages, and server information.
### HTML/CSS: Frontend markup and styling for the user interface.
### JavaScript: Used for client-side interactivity and real-time messaging through WebSocket communication.
### Bootstrap: Frontend framework for responsive and visually appealing design.
jQuery: JavaScript library for simplifying DOM manipulation and AJAX requests.
## Installation
Clone the repository:

bash
Copy code
git clone https://github.com/yourusername/chatchirp.git
Install dependencies:

Copy code
pip install -r requirements.txt
Run the application:

Copy code
python app.py
Access the application in your web browser at http://localhost:5000.

## Configuration
Configure the Flask application by modifying the config.py file to set parameters such as secret key, database URI, etc.
Ensure proper security measures are taken, such as using HTTPS for production deployments and configuring secure cookie settings.
## Usage
Sign up for an account if you are a new user, or log in with your existing credentials.
Edit your profile to customize your username, email, and profile picture.
Start a personal chat by selecting a user from the list of online users, or create a new server for group chatting.
Engage in conversations by sending messages within personal chats or server channels.
Enjoy real-time messaging with other users!
