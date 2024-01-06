from flask import Flask, render_template, url_for, flash, session, request, redirect
from wtforms import Form, StringField, PasswordField, TextAreaField, SubmitField, validators
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import pbkdf2_sha256
from datetime import datetime

    

#application init and configurations
app = Flask(__name__)
app.secret_key = 'lamePass1234'  #TODO - change to environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://Blogz:Blogz1234D!@localhost:3306/blogz"  
app.config['SQLALCHEMY_ECHO'] = True


#initialize instance of db
db = SQLAlchemy(app)


#<<<<<------------------------Models----------------------->>>>>
#user model
class User(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30))
    email = db.Column(db.String(120))
    password = db.Column(db.String(120))
    #init a user
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
    #reppin again....
    def __repr__(self):
        return self.username


#blog model
class Blog(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime, nullable=False,
        default=datetime.utcnow)
    user_name = db.Column(db.String(30))
    #init a post
    def __init__(self, title, body, user_name):
        self.title = title
        self.body = body
        self.user_name = user_name
    #reppin again....
    def __repr__(self):
        return (self.title, self.body)


#<<<<------------------------Forms--------------------->>>>
#Registration form
class RegistrationForm(Form): 
    username = StringField('Username', [validators.Length(min=6, max=30), validators.DataRequired()])
    email = StringField('Email', [validators.Length(max=120), validators.DataRequired()])
    password = PasswordField('Password', [validators.Length(min=7), validators.DataRequired()])
    verify = PasswordField('Verify Password', [validators.DataRequired()])
    submit = SubmitField('Submit')


#Login form
class LoginForm(Form): 
    username = StringField('Username', [validators.Length(min=6, max=30), validators.DataRequired()])
    password = PasswordField('Password', [validators.Length(min=7), validators.DataRequired()])
    submit = SubmitField('Submit')


#create a blog form
class BlogForm(Form):
    title = StringField('Title', [validators.Length(min=6, max=120)])
    body = TextAreaField('Body', [validators.Length(min=20)])






#<<<<<--------------------------Routes------------------------>>>>>
#logout user
@app.route('/logout')
def logout():
    session.pop('username', None)
    session['logged_in'] = False
    flash('You have been logged out!', 'success')
    return redirect(url_for('home'))



@app.route('/user/<string:user_name>/', methods=['GET', 'POST'])
def user(user_name):
    blogs = Blog.query.filter_by(user_name=user_name).all()
    return render_template('user.html', title=user_name, blogs=blogs, username=user_name)



#login to account
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        hashed = existing_user.password
        if pbkdf2_sha256.verify(password, hashed):
            session['username'] = existing_user.username
            session['logged_in'] = True
            flash('You are now logged in!', 'success')
            return redirect('/')
        elif not existing_user:
            flash('Error with your username!', 'danger')
            return redirect(url_for('login'))
        else:
            flash('Password is incorrect', 'danger')
            return redirect(url_for('login'))
    else:
        return render_template('login.html', title='Login!', form=form)



#signup for an account
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()
        if password != verify:
            flash('Your passwords do not match, try again!', 'danger')
            return redirect(url_for('signup'))
        if not existing_email or not existing_user:
            new_user = User(username, email, pbkdf2_sha256.hash(password))
            db.session.add(new_user)
            db.session.commit()
            session['username'] = new_user.username
            session['logged_in'] = True
            return redirect('/')
        elif len(existing_user) > 0:  
            flash('That username is already in use, try again!', 'danger')
            return redirect(url_for('signup'))
        elif len(existing_email) > 0:
            flash('That email is already in use, try again!', 'danger')
            return redirect(url_for('signup'))
    else:
        return render_template('signup.html', title='Signup!', form=form)



#display a single blog post by ID query
@app.route('/blog/<int:id>/', methods=['GET', 'POST'])
def blog(id):
    blog = Blog.query.get(id)
    return render_template('blog.html', title=blog.title, blog=blog)



#create a new blog post with error checking
@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    form = BlogForm(request.form)
    if request.method == 'POST':
        title = request.form['title'] 
        body = request.form['body']
        if len(title) < 1:
            flash('You must add a title!', 'danger')
            redirect(url_for('newpost'))
        elif len(body) < 1:
            flash('You must provide content to the body!', 'danger')
            redirect(url_for('newpost'))
        else:  
            username = session['username']
            user = User.query.filter_by(username=username).first()
            blog = Blog(title, body, user.username)
            db.session.add(blog)
            db.session.commit()
            last_item = Blog.query.order_by(Blog.id.desc()).first()
            id = last_item.id
            return render_template('blog.html', blog=blog)
    return render_template('newpost.html', title='Add and Entry', form=form)



#home - landing page route
@app.route('/home')
def home():
    blog = Blog.query.order_by(Blog.pub_date.desc()).all()
    return render_template('home.html', title='Blogz Index', blogs=blog)



@app.route('/')
def index():
    users = User.query.order_by(User.username.asc()).all()
    return render_template('index.html', title="Index", users=users)



@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')











#<<<-------------------------------------------------------->>>
if __name__ == '__main__':
    app.run(debug=True)