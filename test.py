import unittest
from app import app, db, Image

class TestImageAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_upload_image(self):
        with open('test.jpg', 'rb') as img:
            response = self.client.post('/upload', data={
                'image': img,
                'metadata': '{"tags": ["test"]}'
            })
        self.assertEqual(response.status_code, 201)

    def test_list_images(self):
        response = self.client.get('/images')
        self.assertEqual(response.status_code, 200)

    def test_view_image(self):
        # Add an image to test database
        image = Image(filename='test.jpg', metadata='{}')
        db.session.add(image)
        db.session.commit()

        response = self.client.get(f'/image/{image.id}')
        self.assertEqual(response.status_code, 200)

    def test_delete_image(self):
        # Add an image to test database
        image = Image(filename='test.jpg', metadata='{}')
        db.session.add(image)
        db.session.commit()

        response = self.client.delete(f'/image/{image.id}')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
