from flask import Flask, request, jsonify
import face_recognition
import os
import io
import base64

app = Flask(__name__)

# ── Home Page ────────────────────────────────────────────────
@app.route('/')
def home():
    return "Face Recognition Server is running. Use POST /upload to send images."

# ── Debug route to return last uploaded image as Base64 ──────
@app.route('/debug/last_image', methods=['GET'])
def last_image():
    try:
        with open('last_upload.jpg', 'rb') as f:
            data = f.read()
        b64 = base64.b64encode(data).decode('utf8')
        return jsonify({'image_b64': b64})
    except FileNotFoundError:
        return jsonify({'error': 'No upload yet'}), 404

# ── Load known faces at startup ──────────────────────────────
known_encodings = []
known_names = []

os.makedirs('known_faces', exist_ok=True)
for fname in os.listdir('known_faces'):
    if fname.lower().endswith(('.jpg', '.png')):
        img = face_recognition.load_image_file(f'known_faces/{fname}')
        encs = face_recognition.face_encodings(img)
        if encs:
            known_encodings.append(encs[0])
            known_names.append(os.path.splitext(fname)[0])

# ── Upload endpoint for ESP32-CAM ────────────────────────────
@app.route('/upload', methods=['POST'])
def upload_image():
    print("=== /upload called ===")
    print("Form fields:", request.files.keys())

    if 'image' not in request.files:
        print("❌ No image field!")
        return jsonify({'result': 'No image part'}), 400

    file = request.files['image']
    data = file.read()
    print(f"Received '{file.filename}' ({len(data)} bytes)")
    # Save for inspection
    with open('last_upload.jpg', 'wb') as f:
        f.write(data)
        print("✅ Saved last_upload.jpg")

    # Face recognition
    img = face_recognition.load_image_file(io.BytesIO(data))
    encs = face_recognition.face_encodings(img)
    if not encs:
        print("❌ No face detected")
        return jsonify({'result': 'No face detected'})

    matches = face_recognition.compare_faces(known_encodings, encs[0])
    if True in matches:
        name = known_names[matches.index(True)]
        print(f"✅ Face recognized: {name}")
        return jsonify({'result': f'Face recognized: {name}'})
    else:
        print("❌ Intruder detected")
        return jsonify({'result': 'Intruder detected'})

# ── Run Server ───────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
