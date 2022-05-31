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




google = oauth.register(
    name='google',
    client_id='762534377906-bfbf53hdq8e6h1prf1fhv5dalecmeso6.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid profile email'},
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
)


@app.route('/login/google')
def google_login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    print('in the authorize!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 11')
    google = oauth.create_client('google')
    print(' 2in the authorize!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 11')

    token = google.authorize_access_token()
    print('3in the authorize!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 11')

    resp = google.get('userinfo')
    print(resp.json(), 'response in route WTF&&&&&&&&&&&&&&&&&&&&&&&&&&')
    # resp.raise_for_status()
    profile = resp.json()
    # do something with the token and profile
    print(profile['email'], '\n!!!!!!!!!!!!!!!!!!!!', token, '\n!!!!!!!!!!!!!')
    user = User.query.filter(User.email == profile['email']).first()
    login_user(user)
    print(current_user.is_authenticated, '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!(((##################')

    return redirect("http://localhost:3000", 302)
    # return url_for('auth.login')
