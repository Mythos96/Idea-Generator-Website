from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import random
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<User {self.id}>'
    
class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    idea_text = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f'<Idea {self.id}>'
    
@app.route('/', methods=['GET', 'POST'])
def index():
    button = request.form.get('button')
    img_click = request.form.get('img_click')

    db.create_all()
    admin_user = User(id=0, email='admin@gmail.com', password='admin')
    db.session.add(admin_user)
    db.session.commit()

    if img_click == 'True':
        return redirect('/login')

    with open("Ideas.txt", "r", encoding="utf-8") as file:
        ideas = file.readlines() 
    random_idea = random.choice(ideas)

    return render_template("index.html", random_idea=random_idea, button=button, img_click=img_click)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        login_email = request.form.get('email')
        login_password = request.form.get('password')

        user_db = User.query.all()
        for user in user_db:
            if login_email == user.email and login_password == user.password:
                session['user_id'] = user.id
                return redirect('/loggedin')

        error = 'Invalid email or password'
        return render_template('/login.html', error=error)

    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_db = User.query.all()

        for user in user_db:
            if email != user.email:
                user = User(email=email, password=password)
                db.session.add(user)
                db.session.commit()
                return redirect('/login')
            else:
                error = 'Email already exists'
                return render_template('/register.html', error=error)
    else:
        return render_template("register.html")
    
@app.route('/loggedin')
def loggedin():
    return render_template("loggedin.html")

@app.route('/profile_settings', methods=['GET', 'POST'])
def profile_settings():
    error = ''
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    delete_account = request.form.get('delete')
    list_users = request.form.get('list')

    if list_users == 'list': 
        if user_id == 0:
            return redirect('/list_users')
        else:
            error = 'You do not have permission to view this page'
            return render_template('profile_settings.html', error=error)
    
    if delete_account == 'delete':
        db.session.delete(user)
        db.session.commit()
        session.pop('user_id', None)
        return redirect('/')

    return render_template("profile_settings.html", user=user)

@app.route('/list_users', methods=['GET', 'POST'])
def list_users():
    users = User.query.all()
    return render_template('list_users.html', users=users)

@app.route('/create_idea', methods=['GET', 'POST'])
def create_idea():
    user_id = session['user_id']
    user_ideas = Idea.query.filter_by(user_id=user_id).all()

    if request.method == 'POST':
        idea_text = request.form.get('idea')

        with open("Ideas.txt", "a", encoding="utf-8") as file:
            file.write(idea_text + "\n")

        new_idea = Idea(user_id=user_id, idea_text=idea_text)
        db.session.add(new_idea)
        db.session.commit()

        return redirect('/create_idea')

    return render_template('create_idea.html', ideas=user_ideas)

@app.route('/delete_idea/<int:idea_id>', methods=['POST'])
def delete_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    if idea.user_id == session['user_id']:
        db.session.delete(idea)
        db.session.commit()

        with open("Ideas.txt", "r", encoding="utf-8") as file:
            lines = file.readlines()
        with open("Ideas.txt", "w", encoding="utf-8") as file:
            for line in lines:
                if line.strip() != idea.idea_text:
                    file.write(line)

    return redirect('/create_idea')

with app.app_context():
    db.create_all()

app.secret_key = 'key'

if __name__ == '__main__':
    app.run(debug=True)