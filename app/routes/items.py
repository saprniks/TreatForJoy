from flask import Blueprint, request, jsonify
from app.utils.db import get_db_session
from app.models import Item

items_bp = Blueprint('items', __name__)

@items_bp.route('/albums/<int:album_id>/items', methods=['GET'])
def get_items(album_id):
    with get_db_session() as session:
        items = session.query(Item).filter_by(album_id=album_id, is_visible=True).all()
        return jsonify([item.to_dict() for item in items])

@items_bp.route('/items/<int:id>', methods=['GET'])
def get_item(id):
    with get_db_session() as session:
        item = session.query(Item).filter_by(id=id, is_visible=True).first()
        if item:
            return jsonify(item.to_dict())
        return jsonify({"error": "Item not found"}), 404

# Add POST, PUT, DELETE routes for creating, updating, and deleting items here
