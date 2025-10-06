"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
Refactor: unified JSON responses, proper HTTP codes, rollback on DB errors,
consistent target_type values, and safer DB access.
"""
import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planets, People, Favorites
from sqlalchemy import select

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)


def search_favorites_list(fav_type, fav_id, user_id):
    """
    Return the Favorites row or None for the given target type/id and user.
    fav_type should be consistent strings like "people" or "planets".
    """
    return db.session.execute(
        select(Favorites).where(
            Favorites.target_type == fav_type,
            Favorites.target_id == fav_id,
            Favorites.user_id == user_id
        )
    ).scalar_one_or_none()


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def handle_hello():
    return jsonify({"msg": "Hello, this is your GET /user response"}), 200


@app.route('/users', methods=['GET'])
def get_all_users_route():
    users = User.query.all()
    if not users:
        return jsonify([]), 200
    return jsonify([u.serialize() for u in users]), 200


@app.route('/user/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites_route(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": f"No user with id {user_id}"}), 404

    return jsonify([fav.serialize() for fav in user.favorites_list]), 200


@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])# poner favs
def post_user_favorite_planet_route(planet_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Invalid request: 'user_id' is required"}), 400

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": f"No user with id {user_id}"}), 404

    planet = db.session.get(Planets, planet_id)
    if planet is None:
        return jsonify({"error": f"No planet with id {planet_id}"}), 404

    if search_favorites_list("planets", planet_id, user_id):
        return jsonify({"error": f"{planet.name} is already in favorites"}), 409

    try:
        favorite = Favorites(
            target_type="planets",
            target_id=planet_id,
            target_name=planet.name,
            user_id=user_id,
            user=user
        )
        db.session.add(favorite)
        db.session.commit()
        return jsonify({"message": f"Added {planet.name} to favorites", "favorite": favorite.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error while adding favorite", "details": str(e)}), 500


@app.route('/favorite/people/<int:person_id>', methods=['POST']) #fav peoplle
def post_user_favorite_people_route(person_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Invalid request: 'user_id' is required"}), 400

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": f"No user with id {user_id}"}), 404

    person = db.session.get(People, person_id)
    if person is None:
        return jsonify({"error": f"No person with id {person_id}"}), 404

    if search_favorites_list("people", person_id, user_id):
        return jsonify({"error": f"{person.name} is already in favorites"}), 409

    try:
        favorite = Favorites(
            target_type="people",
            target_id=person_id,
            target_name=person.name,
            user_id=user_id,
            user=user
        )
        db.session.add(favorite)
        db.session.commit()
        return jsonify({"message": f"Added {person.name} to favorites", "favorite": favorite.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error while adding favorite", "details": str(e)}), 500


@app.route('/people', methods=['GET'])
def get_all_people_route():
    people = People.query.all()
    return jsonify([p.serialize() for p in people]), 200


@app.route('/planets', methods=['GET'])
def get_all_planets_route():
    planets = Planets.query.all()
    return jsonify([p.serialize() for p in planets]), 200


@app.route('/people/<int:person_id>', methods=['GET'])
def get_one_person_route(person_id):
    person = People.query.get(person_id)
    if person is None:
        return jsonify({"error": f"Person with id {person_id} not found"}), 404
    return jsonify(person.serialize()), 200


@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_one_planet_route(planet_id):
    planet = Planets.query.get(planet_id)
    if planet is None:
        return jsonify({"error": f"Planet with id {planet_id} not found"}), 404
    return jsonify(planet.serialize()), 200


@app.route('/favorite/people/<int:person_id>/<int:user_id>', methods=['DELETE'])#borrar fav
def delete_user_favorite_people_route(person_id, user_id):
    fav = search_favorites_list("people", person_id, user_id)
    if fav is None:
        return jsonify({"error": "Favorite not found"}), 404

    try:
        db.session.delete(fav)
        db.session.commit()
        return jsonify({"message": f"Deleted {fav.target_name} from favorites"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error while deleting favorite", "details": str(e)}), 500


@app.route('/favorite/planets/<int:planet_id>/<int:user_id>', methods=['DELETE']) 
def delete_user_favorite_planet_route(planet_id, user_id):
    fav = search_favorites_list("planets", planet_id, user_id)
    if fav is None:
        return jsonify({"error": "Favorite not found"}), 404

    try:
        db.session.delete(fav)
        db.session.commit()
        return jsonify({"message": f"Deleted {fav.target_name} from favorites"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error while deleting favorite", "details": str(e)}), 500


@app.route('/user/<int:user_id>', methods=['DELETE'])#borrar user
def delete_user_route(user_id):
    user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        return jsonify({"error": f"User with id {user_id} not found"}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"Deleted user {user.email}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error while deleting user", "details": str(e)}), 500


if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
