import os
import yaml
import json
from datetime import datetime
from flask import Flask, request, session, g, redirect, render_template, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy.exc import SQLAlchemyError
from requests_oauthlib import OAuth1Session
from oauth_wiki import get_username


__dir__ = os.path.dirname(__file__)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
app.config['SQLALCHEMY_BINDS'] = {'cities': 'sqlite:///cities.db',
                                  'schools': 'sqlite:///schools.db',
                                  'users': 'sqlite:///users.db'}
app.config.update(yaml.safe_load(open(os.path.join(__dir__, 'config.yaml'))))

db = SQLAlchemy(app)
key = app.config["ENCRYPTION_KEY"]


########################################################################################################################
# C L A S S E S   &   F O R M S
########################################################################################################################
class City(db.Model):
    __tablename__ = 'cities'
    __bind_key__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    school = db.relationship("School")


class School(db.Model):
    __tablename__ = 'schools'
    __bind_key__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    city = db.Column(db.Integer, db.ForeignKey('cities.id'))
    user = db.relationship("User")

    def __repr__(self):
        return '{}'.format(self.name)


class User(db.Model):
    __tablename__ = 'users'
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StringEncryptedType(db.String(150), key), nullable=False, unique=True)
    school = db.Column(StringEncryptedType(db.Integer, key), db.ForeignKey('schools.id'), nullable=False)
    date_consent = db.Column(db.DateTime, default=datetime.utcnow())


########################################################################################################################
# L O G I N
########################################################################################################################
@app.before_request
def init_profile():
    g.profiling = []


@app.before_request
def global_user():
    g.user = get_username()


@app.route('/login')
def login():
    """
    This function creates an OAuth session and sends the user
    to the authorization special webpage in ptwikiversity so
    the user can give permission for the tool to operate.

    :return: redirects the user to the authorization special
    webpage on ptwikiversity.
    """

    next_page = request.args.get('next')

    if next_page:
        session['after_login'] = next_page

    client_key = app.config['CONSUMER_KEY']
    client_secret = app.config['CONSUMER_SECRET']

    base_url = 'https://pt.wikiversity.org/w/index.php'
    request_token_url = base_url + '?title=Special%3aOAuth%2finitiate'

    oauth = OAuth1Session(client_key,
                          client_secret=client_secret,
                          callback_uri='oob')

    fetch_response = oauth.fetch_request_token(request_token_url)

    session['owner_key'] = fetch_response.get('oauth_token')
    session['owner_secret'] = fetch_response.get('oauth_token_secret')

    base_authorization_url = 'https://pt.wikiversity.org/wiki/Special:OAuth/authorize'
    authorization_url = oauth.authorization_url(base_authorization_url,
                                                oauth_consumer_key=client_key)

    return redirect(authorization_url)


@app.route("/oauth-callback", methods=["GET"])
def oauth_callback():
    """
    This function stores the authorization tokens of the
    users and redirects them to the page they were before
    the logging in process.

    :return: redirects the users to the page they were
    before logging in and authorizating the tool.
    """

    base_url = 'https://pt.wikiversity.org/w/index.php'
    client_key = app.config['CONSUMER_KEY']
    client_secret = app.config['CONSUMER_SECRET']

    oauth = OAuth1Session(client_key,
                          client_secret=client_secret,
                          resource_owner_key=session['owner_key'],
                          resource_owner_secret=session['owner_secret'])

    oauth_response = oauth.parse_authorization_response(request.url)
    verifier = oauth_response.get('oauth_verifier')
    access_token_url = base_url + '?title=Special%3aOAuth%2ftoken'

    oauth = OAuth1Session(client_key,
                          client_secret=client_secret,
                          resource_owner_key=session['owner_key'],
                          resource_owner_secret=session['owner_secret'],
                          verifier=verifier)

    oauth_tokens = oauth.fetch_access_token(access_token_url)
    session['owner_key'] = oauth_tokens.get('oauth_token')
    session['owner_secret'] = oauth_tokens.get('oauth_token_secret')
    next_page = session.get('after_login')

    return redirect(next_page)


########################################################################################################################
# R O U T E S
########################################################################################################################
@app.route('/')
def home():
    username = get_username()
    registered = False

    if username:
        participant = User.query.filter_by(name=username).first()
        if participant:
            registered = True

    return render_template('home.html',
                           username=username,
                           registered=registered)


@app.route('/inscricao', methods=["POST", "GET"])
def subscription():
    username = get_username()
    if request.method == "POST":
        if not check_if_user_exists_in_db(username):
            form = request.form
            school = form.get("school")
            new_user = User(name=username, school=school, date_consent=datetime.utcnow())
            try:
                db.session.add(new_user)
                db.session.commit()
            except SQLAlchemyError as e:
                error = "Aconteceu um erro!<br>Tente novamente, se o erro persistir, comunique o código abaixo por" \
                        "email para wikilovesbahia@wmnobrasil.org<br><br>" + str(e)
                return error
        return redirect(url_for('home'))  # TODO: Redirect to manage_user page
    else:
        cities = [{"id": city.id, "name": city.name} for city in City.query.all()]
        return render_template('subscription.html', username=username, cities=cities)


def check_if_user_exists_in_db(username):
    user = User.query.filter_by(name=username).first()
    if user:
        return True
    else:
        return False


@app.route('/pegar-escola', methods=['POST'])
def getschool():
    if request.method == "POST":
        city_id = request.form.get('city')
        if city_id:
            schools = [{"id": school.id, "name": school.name} for school in School.query.filter_by(city=int(city_id))]
            response = make_response(json.dumps(schools))
            response.content_type = 'application/json'
            return response
        else:
            return ""
    else:
        return redirect(url_for("home"))


@app.route('/deletar_cadastro', methods=["POST"])
def delete_user():
    username = get_username()
    form = request.form
    delete = form["delete"]
    if delete:
        user = User.query.filter_by(name=username).first()
        if user:
            try:
                db.session.delete(user)
                db.session.commit()
            except SQLAlchemyError as e:
                error = "Aconteceu um erro!<br>Tente novamente, se o erro persistir, comunique o código abaixo " \
                        "por email para wikilovesbahia@wmnobrasil.org<br><br>" + str(e)
                return error
        return redirect(url_for("home"))
    else:
        return redirect(url_for("update_user"))


@app.route('/atualizar-cadastro', methods=["GET", "POST"])
def update_user():
    username = get_username()

    if request.method == "GET":
        user = User.query.filter_by(name=username).first()
        if user:
            school_id = user.school
            user_school = School.query.get(school_id)
            city_id = user_school.city
            user_city = City.query.get(city_id)

            cities = [{"id": city.id, "name": city.name, "selected": city.id == city_id}
                      for city in City.query.all()]

            return render_template("update_user.html",
                                   user=user,
                                   user_city=user_city,
                                   user_school=user_school,
                                   cities=cities)
        else:
            return redirect(url_for('subscription'))
    else:
        form = request.form
        new_school = form["school"]
        user = User.query.filter_by(name=username).first()
        if user:
            user.school = new_school
            try:
                db.session.commit()
            except SQLAlchemyError as e:
                error = "Aconteceu um erro!<br>Tente novamente, se o erro persistir, comunique o código abaixo " \
                        "por email para wikilovesbahia@wmnobrasil.org<br><br>" + str(e)
                return error
            return redirect(url_for("update_user"))
        return redirect(url_for("home"))


if __name__ == '__main__':
    app.run()
