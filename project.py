#!/usr/bin/python

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Sport, Item, User
# importing login tools
from flask import session as login_session
import random, string

# IMPORTS FOR THIS STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super secret key'

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"

engine = create_engine('sqlite:///sports.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

#Get User Array
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user
# Authorize Sport Author
def getAuthor(id):
    author = session.query(Sport).filter_by(id=id).one()
    return author

def getItemAuthor(id):
    author = session.query(Item).filter_by(id=id).one()
    return author

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/sports/')
def showSports():
	# Check if user is logged in
    if 'username' not in login_session:
        return redirect('/login')
    sports = session.query(Sport).all()
    return render_template(
        'sports.html',
        sports=sports,)


# New Sport
@app.route('/sports/new', methods=['GET', 'POST'])
def newSport():
    if request.method == 'POST':
        newSport = Sport(name=request.form['name'], description=request.form[
                           'description'], user_id = login_session['user_id'])
        session.add(newSport)
        session.commit()
        return redirect(url_for('showSports'))
    else:
        return render_template('newsport.html')


# Edit Sport
@app.route('/sports/<int:sport_id>/edit',
           methods=['GET', 'POST'])
def editSport(sport_id):
	# Get author of item
    author = getAuthor(sport_id)
	# Check if logged in user is author of the sport
    if author.user_id != login_session['user_id']:
        return redirect('/login')
    editedSport = session.query(Sport).filter_by(id=sport_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedSport.name = request.form['name']
            editedSport.description = request.form['description']
            editedSport.id = Sport.id
        session.add(editedSport)
        session.commit()
        return redirect(url_for('showSports'))
    else:
        return render_template(
            'editsport.html', sport_id=sport_id)


# Delete Sport
@app.route('/sports/<int:sport_id>/delete',
           methods=['GET', 'POST'])
def deleteSport(sport_id):
	# Get author of item
    author = getAuthor(sport_id)
	# Check if logged in user is author of the sport
    if author.user_id != login_session['user_id']:
        return redirect('/login')
    sportToDelete = session.query(Sport).filter_by(id=sport_id).one()
    if request.method == 'POST':
        session.delete(sportToDelete)
        session.commit()
        return redirect(url_for('showSports'))
    else:
        return render_template(
            'deletesport.html', sport_id=sport_id)


# Single Sport Page
@app.route('/sports/<int:sport_id>/items')
def sportItems(sport_id):
    sport = session.query(Sport).filter_by(id=sport_id).one()
    items = session.query(Item).filter_by(sport_id=sport_id)
    return render_template(
        'items.html', sport=sport, items=items, sport_id=sport_id)


# New Item
@app.route('/sports/<int:sport_id>/new', methods=['GET', 'POST'])
def newItem(sport_id):
	# Check if user is logged in
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(name=request.form['name'], description=request.form[
                           'description'], sport_id=sport_id, user_id = login_session['user_id'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('sportItems', sport_id=sport_id))
    else:
        return render_template('newitem.html', sport_id=sport_id)


# Edit Item
@app.route('/sports/<int:sport_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(sport_id, item_id):
	# Get author of item
    author = getItemAuthor(item_id)
	# Check if logged in user is author of the sport
    if author.user_id != login_session['user_id']:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            editedItem.id = Item.id
        session.add(editedItem)
        session.commit()
        return redirect(url_for('sportItems'))
    else:
        return render_template(
            'edititem.html', sport_id=sport_id, item_id=item_id)


# Delete Item
@app.route('/sports/<int:sport_id>/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(sport_id, item_id):
	# Get author of item
    author = getItemAuthor(item_id)
	# Check if logged in user is author of the sport
    if author.user_id != login_session['user_id']:
        return redirect('/login')
    itemToDelete = session.query(Sport).filter_by(id=sport_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('sports'))
    else:
        return render_template(
            'deleteitem.html', sport_id=sport_id, item_id=item_id)


@app.route('/')
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('/login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if user exists
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return "Login Successful"


@app.route('/logout')
def logout():

    if login_session:
        gdisconnect()
        del login_session['gplus_id']
        del login_session['access_token']

        del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['provider']

    return redirect(url_for('login'))


# JSON endpoint for all sports
@app.route('/sports/JSON')
def sportsJSON(sport_id):
    sports = session.query(Sport).all()
    return jsonify(Items=[i.serialize for i in items])


# JSON endpoint for a single sport
@app.route('/sports/<int:sport_id>/sport/JSON')
def sportJSON(sport_id):
    sport = session.query(Sport).filter_by(id=sport_id).one()
    items = session.query(Item).filter_by(
        sport_id=sport_id).all()
    return jsonify(Items=[i.serialize for i in items])


# JSON endpoint for a single item
@app.route('/sports/<int:sport_id>/<int:item_id>/JSON')
def itemJSON(sport_id):
    sport = session.query(Sport).filter_by(id=sport_id).one()
    items = session.query(Item).filter_by(
        item_id=item_id).one()
    return jsonify(Items=[i.serialize for i in items])


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
