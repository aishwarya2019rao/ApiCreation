from flask import Flask, request, jsonify, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///images.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Model
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    image_metadata = db.Column(db.JSON, nullable=False)  # Renamed from metadata
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/upload', methods=['POST'])
def upload_image():
    if request.method == 'GET':
        return jsonify({"message": "Please use POST to upload an image"}), 405
    if 'image' not in request.files or not request.json.get('metadata'):
        return jsonify({'error': 'Image and metadata are required'}), 400

    image = request.files['image']
    metadata = request.json.get('metadata')

    if image.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(image.filename):
        return jsonify({'error': 'Unsupported file type'}), 400

    filename = save_file(image)
    new_image = Image(filename=filename, image_metadata=metadata)  # Use image_metadata here
    db.session.add(new_image)
    db.session.commit()

    return jsonify({'status': 'success', 'image_id': new_image.id}), 201

@app.route('/images', methods=['GET'])
def list_images():
    tag_filter = request.args.get('tag')
    date_filter = request.args.get('date_uploaded')

    query = Image.query
    if tag_filter:
        query = query.filter(Image.image_metadata['tags'].contains([tag_filter]))  # Use image_metadata here
    if date_filter:
        try:
            date_filter = datetime.strptime(date_filter, '%Y-%m-%d')
            query = query.filter(db.func.date(Image.upload_date) == date_filter.date())
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    images = query.all()
    response = [{'id': img.id, 'filename': img.filename, 'metadata': img.image_metadata, 'upload_date': img.upload_date.isoformat()} for img in images]
    return jsonify(response), 200

### View/Download Image
@app.route('/image/<int:image_id>', methods=['GET'])
def get_image(image_id):
    action = request.args.get('action', 'view')
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Image file not found'}), 404

    if action == 'download':
        return send_from_directory(app.config['UPLOAD_FOLDER'], image.filename, as_attachment=True)
    return send_from_directory(app.config['UPLOAD_FOLDER'], image.filename)

## Delete Image
@app.route('/image/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(image)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Image deleted'}), 200

# Helpers
def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file):
    filename = f"{datetime.timestamp()}_{file.filename}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename

# Run Application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if not exist
    app.run(debug=True)
