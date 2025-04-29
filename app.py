from flask import Flask, request, jsonify
import face_recognition
import os

app = Flask(__name__)

# ── Optional Home Page ─────────────────────────────────────
@app.route('/')
def home():
    return "Face Recognition Server is running. Use POST /upload to send images."

# ── Load known faces at startup ────────────────────────────
known_encodings = []
known_names = []

if not os.path.exists('known_faces'):
    os.makedirs('known_faces')

for fname in os.listdir('known_faces'):
    if fname.lower().endswith(('.jpg', '.png')):
        img = face_recognition.load_image_file(f'known_faces/{fname}')
        enc = face_recognition.face_encodings(img)
        if enc:
            known_encodings.append(enc[0])
            known_names.append(os.path.splitext(fname)[0])  # Filename without extension

# ── Upload endpoint for ESP32-CAM ──────────────────────────
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'result': 'No image part'}), 400

    file = request.files['image']
    img = face_recognition.load_image_file(file)
    encs = face_recognition.face_encodings(img)

    if not encs:
        return jsonify({'result': 'No face detected'})

    matches = face_recognition.compare_faces(known_encodings, encs[0])
    if True in matches:
        idx = matches.index(True)
        return jsonify({'result': f'Face recognized: {known_names[idx]}'})
    else:
        return jsonify({'result': 'Intruder detected'})

# ── Run on Railway's provided PORT ─────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
