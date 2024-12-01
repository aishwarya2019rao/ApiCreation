# ApiCreation
# Image Management API

## Endpoints

### 1. Upload Image
**POST** `/upload`  
**Body (form-data)**:  
- `image` (file): Image file to upload.  
- `metadata` (string): JSON metadata.

### 2. List Images
**GET** `/images`  
**Query Parameters**:  
- `tag`: Filter by tag.  
- `date`: Filter by upload date (YYYY-MM-DD).

### 3. View/Download Image
**GET** `/image/<image_id>`  

### 4. Delete Image
**DELETE** `/image/<image_id>`  

## Testing
Run the unit tests:
```bash
python tests.py
