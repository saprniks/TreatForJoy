from flask import Blueprint, request, jsonify
from app.utils.db import get_db_session
from app.models import Album, Item

albums_bp = Blueprint('albums', __name__)

@albums_bp.route('/albums', methods=['GET'])
def get_albums():
    with get_db_session() as session:
        albums = session.query(Album).filter_by(is_visible=True).all()
        return jsonify([album.to_dict() for album in albums])

@albums_bp.route('/albums/<int:id>', methods=['GET'])
def get_album(id):
    with get_db_session() as session:
        album = session.query(Album).filter_by(id=id, is_visible=True).first()
        if album:
            return jsonify(album.to_dict())
        return jsonify({"error": "Album not found"}), 404

# Add POST, PUT, DELETE routes for creating, updating, and deleting albums here
