import face_recognition
import os

# Point this at whatever image you just saved in known_faces/
img_path = 'known_faces/cbimage.jpg'
if not os.path.exists(img_path):
    raise FileNotFoundError(f"Put your image at {img_path}")

# 1. Load the image
image = face_recognition.load_image_file(img_path)

# 2. Detect face locations
locations = face_recognition.face_locations(image)  
#    → returns a list of (top, right, bottom, left) tuples

# 3. Compute encodings at those locations
encodings = face_recognition.face_encodings(image, locations)

print(f"Found {len(locations)} face(s) at {locations}")
print(f"Computed {len(encodings)} encoding(s).")
