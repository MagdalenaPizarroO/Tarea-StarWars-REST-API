"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planets, Fav_People, Fav_Planets
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

@app.route('/people', methods=['GET'])
def get_people():
    get_all_people = People.query.all()
    result = list(map(lambda people: people.serialize(), get_all_people))
    return jsonify(result)

@app.route('/people/<int:people_id>', methods=['GET'])
def get_character(people_id):
    get_character = People.query.get(people_id)
    if(get_character is None):
        return jsonify({"msg": "Character not found"}), 404 
    else:
        return jsonify(get_character.serialize())
    
@app.route('/people', methods=['POST'])
def add_character():
    body = request.get_json()
    new_character = People(name=body['name'])
    # Otra forma de hacerlo es agregar uno por uno:
    # new_people = People()
    # new_people.name = body['name']
    # new_people.gender = body['gender']
    # etc...
    db.session.add(new_character)
    db.session.commit()
    return jsonify({"msg": "New character added"}), 201
#se deben realizar validaciones; ej, si ya existe un personaje con ese nombre, no lo puede agregar; si no tiene nombre, no puede agregar, etc

@app.route('/planets', methods=['GET'])
def get_planets():
    get_all_planets = Planets.query.all()
    result = list(map(lambda planet: planet.serialize(), get_all_planets))
    return jsonify(result)

@app.route('/planets/<int:planets_id>', methods=['GET'])
def get_planet(planets_id):
    get_planet = Planets.query.get(planets_id)
    if(get_planet is None):
        return jsonify({"msg": "Planet not found"}), 404 
    else:
        return jsonify(get_planet.serialize())

@app.route('/users', methods=['GET'])
def get_users():
    all_users = User.query.all()
    result = list(map(lambda user: user.serialize(), all_users))
    return jsonify(result)

@app.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_favorites(user_id):
    one_user = User.query.get(user_id)
    fav_character = Fav_People.query.filter_by(user_id=user_id).all()
    fav_char_serialized = list(map(lambda favorite: favorite.serialize(),fav_character))
    fav_planet = Fav_Planets.query.filter_by(user_id=user_id).all()
    fav_planets_serialized = list(map(lambda favorite: favorite.serialize(),fav_planet))
    return jsonify({
        "user_id" : one_user.id,
        "favorite_people": fav_char_serialized,
        "favorite_planets": fav_planets_serialized,
    })

@app.route('/users/<int:user_id>/favorites/planets/<int:planets_id>', methods=['POST'])
def add_favoritePlanet(user_id, planets_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"msg": "User not found"}), 404
    planet = Planets.query.get(planets_id)
    if planet is None:
        return jsonify({"msg": "Planet not found"}), 404
    existing_favorite = Fav_Planets.query.filter_by(user_id=user_id, planets_id=planets_id).first()
    if existing_favorite is not None:
        return jsonify({"msg": "Planet is already in favorites"}), 409
    new_fav_planet = Fav_Planets(planets_id=planets_id, user_id=user_id)
    db.session.add(new_fav_planet)
    db.session.commit() 
    return jsonify({"msg": "Planet added to favorites"})

@app.route('/users/<int:user_id>/favorites/people/<int:people_id>', methods=['POST'])
def add_favoritePeople(user_id, people_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"msg": "User not found"}), 404
    character = People.query.get(people_id)
    if character is None:
        return jsonify({"msg": "Character not found"}), 404
    existing_favorite = Fav_People.query.filter_by(user_id=user_id, people_id=people_id).first()
    if existing_favorite is not None:
        return jsonify({"msg": "Character is already in favorites"}), 409
    new_fav_character = Fav_People(people_id=people_id, user_id=user_id)
    db.session.add(new_fav_character)
    db.session.commit()
    return jsonify({"msg": "Character added to favorites"}) 

@app.route('/users/<int:user_id>/favorites/people/<int:people_id>', methods=['DELETE'])
def delete_favoritePeople(user_id, people_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"msg": "User not found"}), 404
    character = People.query.get(people_id)
    if character is None:
        return jsonify({"msg": "Character not found"}), 404
    fav_character = Fav_People.query.filter_by(user_id=user_id, people_id=people_id).first()
    if fav_character is None:
        return jsonify({"msg": "Character not found"}), 404
    #Para eliminar el personaje:
    db.session.delete(fav_character)
    db.session.commit()
    return jsonify({"msg": "Character deleted from favorites"}), 202

@app.route('/users/<int:user_id>/favorites/planets/<int:planets_id>', methods=['DELETE'])
def delete_favoritePlanet(user_id, planets_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"msg": "User not found"}), 404
    planet = Planets.query.get(planets_id)
    if planet is None:
        return jsonify({"msg": "Planet not found"}), 404
    fav_planet = Fav_Planets.query.filter_by(user_id=user_id, planets_id=planets_id).first()
    if fav_planet is None:
        return jsonify({"msg": "Planet not found"}), 404
    #Para eliminar el personaje:
    db.session.delete(fav_planet)
    db.session.commit()
    return jsonify({"msg": "Planet deleted from favorites"}), 202

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
