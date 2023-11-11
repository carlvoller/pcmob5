from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
import os

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath('./db.sqlite')}"
db.init_app(app)

app.config['JWT_SECRET_KEY'] = 'hello'

jwt = JWTManager(app)

@jwt.user_identity_loader
def user_identity_lookup(user):
  return user.json()

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
  identity = jwt_data["sub"]
  return User.query.filter_by(id=identity).first()


class BlogPost(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(80))
  content = db.Column(db.String(400))

  def json(self):
    return {'id': self.id, 'title': self.title, 'content': self.content}

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(100))
  password = db.Column(db.String(100))

  def json(self):
    return { 'id': self.id, 'username': self.username, 'password': self.password }

# Look for all database table models in your app and create any missing tables.
with app.app_context():
  db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == "POST":
    return {'about': 'this is an API for a blog. Get / to read more.'}
  else:
    return render_template("index.html")


@app.route('/create', methods=['POST'])
def create_post():
  json_data = request.get_json()
  title = json_data['title']
  content = json_data['content']

  post = BlogPost(title=title, content=content)

  db.session.add(post)
  db.session.commit()
  return post.json()


@app.route('/post/<int:id>', methods=['GET'])
def get_post(id):

  post = BlogPost.query.get(id) # None

  if post is None:
    print('That post does not exist!')
    return 'Post does not exist!', 404
  else:
    return post.json()

@app.route('/posts', methods=['GET'])
def all_post():
  posts = BlogPost.query.all()
  json_posts = []
  for post in posts:
    json_posts.append(post.json())

  return jsonify(json_posts)


@app.route('/post/<int:id>', methods=['DELETE'])
def delete_post(id):
  
  post = BlogPost.query.get(id)

  if post is None:
    return 'Post does not exist!', 404
  
  db.session.delete(post)
  db.session.commit()

  return {"message": "Post with id " + str(id) + " has been deleted"}


@app.route('/post/<int:id>', methods=['PUT'])
def update_post(id):
  
  post = BlogPost.query.get(id)

  if post is None:
    return 'Post does not exist!', 404
  
  json_data = request.json
  if 'title' in json_data:
    post.title = json_data['title']
  if 'content' in json_data:
    post.content = json_data['content']

  db.session.commit()
  return f"Updated: {post.json()}"

@app.route('/newuser', methods=['POST'])
def newuser():
  json_data = request.get_json()
  username = json_data["username"]
  password = json_data["password"]
  users = User.query.all()
  for u in users:
    if username == u.username:
      return 'User already exists!', 409

  new_user = User(username=username, password=password)
  db.session.add(new_user)
  db.session.commit()

  return f"Successfully created a new user: {username}"

@app.route('/users', methods=['GET'])
def all_users():
  users = User.query.all()
  json_users = []
  for user in users:
    json_users.append(user.json())

  return jsonify(json_users)

@app.route("/login", methods=["POST"])
def login():
  username = request.json["username"]
  password = request.json["password"]

  user = User.query.filter_by(username=username).first()
  if user and password == user.password:
    return jsonify({ 'message': 'Successfully logged in!', 'access_token': create_access_token(identity=user) })
  else:
    return jsonify({ 'message': 'Username or Password is incorrect.' }), 400


  

app.run(host='0.0.0.0', port=8000, debug=True)
