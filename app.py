from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///images.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from models import Image

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files or 'metadata' not in request.form:
        return jsonify({'error': 'Image and metadata are required'}), 400

    image = request.files['image']
    metadata = request.form['metadata']

    if image.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the image
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    image.save(file_path)

    # Save metadata to database
    new_image = Image(filename=image.filename, metadata=metadata)
    db.session.add(new_image)
    db.session.commit()

    return jsonify({'message': 'Image uploaded successfully', 'image_id': new_image.id}), 201

@app.route('/images', methods=['GET'])
def list_images():
    tag_filter = request.args.get('tag')
    date_filter = request.args.get('date')

    query = Image.query
    if tag_filter:
        query = query.filter(Image.metadata.like(f"%{tag_filter}%"))
    if date_filter:
        query = query.filter(db.func.date(Image.upload_date) == date_filter)

    images = query.all()
    response = [{'id': img.id, 'filename': img.filename, 'metadata': img.metadata, 'upload_date': img.upload_date.isoformat()} for img in images]
    return jsonify(response), 200

@app.route('/image/<int:image_id>', methods=['GET'])
def view_image(image_id):
    image = Image.query.get_or_404(image_id)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    return send_file(file_path, as_attachment=True)

@app.route('/image/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    image = Image.query.get_or_404(image_id)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(image)
    db.session.commit()
    return jsonify({'message': 'Image deleted successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)
