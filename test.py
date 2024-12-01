import unittest
from app import app, db, Image
from io import BytesIO
import os
import json

class ImageAPITestCase(unittest.TestCase):
    def setUp(self):
        """Set up the test client and test database."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory DB for testing
        app.config['UPLOAD_FOLDER'] = 'test_uploads'
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        """Clean up the test database and test files."""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
            os.remove(file_path)
        os.rmdir(app.config['UPLOAD_FOLDER'])

    def test_upload_image(self):
        """Test uploading an image with metadata."""
        data = {
            'image': (BytesIO(b"test image content"), 'test_image.jpg'),
            'metadata': 'Sample metadata'
        }
        response = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 201)
        response_data = response.get_json()
        self.assertIn('image_id', response_data)

    def test_list_images(self):
        """Test listing all images with optional filters."""
        # Add some test data
        img1 = Image(filename="image1.jpg", image_metadata="tag1, tag2")
        img2 = Image(filename="image2.jpg", image_metadata="tag2, tag3")
        db.session.add_all([img1, img2])
        db.session.commit()

        response = self.client.get('/images')
        self.assertEqual(response.status_code, 200)
        images = response.get_json()
        self.assertEqual(len(images), 2)

        # Test filtering by tag
        response = self.client.get('/images?tag=tag1')
        self.assertEqual(response.status_code, 200)
        images = response.get_json()
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]['filename'], "image1.jpg")

    def test_view_image(self):
        """Test viewing/downloading an image."""
        # Add a test image
        img = Image(filename="test_image.jpg", image_metadata="metadata")
        db.session.add(img)
        db.session.commit()

        # Simulate image upload
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
        with open(file_path, 'wb') as f:
            f.write(b"test image content")

        response = self.client.get(f'/image/{img.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/octet-stream')

    def test_delete_image(self):
        """Test deleting an image."""
        # Add a test image
        img = Image(filename="test_image.jpg", image_metadata="metadata")
        db.session.add(img)
        db.session.commit()

        # Simulate image upload
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
        with open(file_path, 'wb') as f:
            f.write(b"test image content")

        response = self.client.delete(f'/image/{img.id}')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data['message'], 'Image deleted successfully')

        # Verify the image is deleted from the database and filesystem
        self.assertIsNone(Image.query.get(img.id))
        self.assertFalse(os.path.exists(file_path))

    def test_upload_image_without_metadata(self):
        """Test uploading an image without metadata."""
        data = {
            'image': (BytesIO(b"test image content"), 'test_image.jpg')
        }
        response = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_upload_image_without_file(self):
        """Test uploading metadata without an image file."""
        data = {
            'metadata': 'Sample metadata'
        }
        response = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

if __name__ == '__main__':
    unittest.main()
