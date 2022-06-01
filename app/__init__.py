from http import client
import os
from flask import Flask, render_template, request, session, redirect, url_for
from flask_cors import CORS
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_login import LoginManager, login_user, current_user
from authlib.integrations.flask_client import OAuth

from app.models import User
from app.api.auth_routes import login


from .models import db, User
from .api.user_routes import user_routes
from .api.auth_routes import auth_routes

from .seeds import seed_commands

from .config import Config

app = Flask(__name__)
# Create a registry with OAuth object
oauth = OAuth(app)

# Setup login manager
login = LoginManager(app)
login.login_view = 'auth.unauthorized'


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


# Tell flask about our seed commands
app.cli.add_command(seed_commands)

app.config.from_object(Config)
app.register_blueprint(user_routes, url_prefix='/api/users')
app.register_blueprint(auth_routes, url_prefix='/api/auth')
db.init_app(app)
Migrate(app, db)

# Application Security
CORS(app)


# Since we are deploying with Docker and Flask,
# we won't be using a buildpack when we deploy to Heroku.
# Therefore, we need to make sure that in production any
# request made over http is redirected to https.
# Well.........
@app.before_request
def https_redirect():
    if os.environ.get('FLASK_ENV') == 'production':
        if request.headers.get('X-Forwarded-Proto') == 'http':
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)


@app.after_request
def inject_csrf_token(response):
    response.set_cookie(
        'csrf_token',
        generate_csrf(),
        secure=True if os.environ.get('FLASK_ENV') == 'production' else False,
        samesite='Strict' if os.environ.get(
            'FLASK_ENV') == 'production' else None,
        httponly=True)
    return response


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def react_root(path):
    if path == 'favicon.ico':
        return app.send_static_file('favicon.ico')
    return app.send_static_file('index.html')



# Register a remote application on the OAuth registry via oauth.register method
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],

    # ACCESS_TOKEN_URL: URL to fetch OAuth access token
    access_token_url='https://accounts.google.com/o/oauth2/token',

    # ACCESS_TOKEN_PARAMS: Extra parameters for Access Token endpoint
    access_token_params=None,

    # AUTHORIZE_URL: Endpoint for user authorization
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,

    # A base URL endpoint to make requests simple
    api_base_url='https://www.googleapis.com/oauth2/v1/',

    # Is a dict configuration to pass extra
    # parameters to OAuth1Session or OAuth2Session
    client_kwargs={'scope': 'openid profile email'},

    # jwks_uri: The URL to get provider’s public JWKS(JSON Web Key Set )
    # The JSON Web Key Set (JWKS) is a set of keys containing the public
    # keys used to verify any JSON Web Token (JWT)
    # issued by the authorization server
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
)


@app.route('/login/google')
def google_login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():

    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    profile = resp.json()

    user = User.query.filter(User.email == profile['email']).first()
    if user:
        login_user(user)
    else:
        user = User(
            username=profile['name'],
            email=profile['email'],
            password=token['id_token']
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)

    return redirect("http://localhost:3000", 302)
