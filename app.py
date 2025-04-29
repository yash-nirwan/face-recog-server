from flask import Flask, request, jsonify
import face_recognition
import os

app = Flask(__name__)

# ── Load known faces at startup ──────────────────────────
known_encodings = []
known_names = []
for fname in os.listdir('known_faces'):
    if fname.lower().endswith(('.jpg', '.png')):
        img = face_recognition.load_image_file(f'known_faces/{fname}')
        enc = face_recognition.face_encodings(img)
        if enc:
            known_encodings.append(enc[0])
            # Use filename (without extension) as the person’s name
            known_names.append(os.path.splitext(fname)[0])

# ── Upload endpoint ───────────────────────────────────────
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'result': 'No image part'}), 400
    file = request.files['image']
    img = face_recognition.load_image_file(file)
    encs = face_recognition.face_encodings(img)
    if not encs:
        return jsonify({'result': 'No face detected'})
    # Compare first face against known faces
    matches = face_recognition.compare_faces(known_encodings, encs[0])
    if True in matches:
        idx = matches.index(True)
        return jsonify({'result': f'Face recognized: {known_names[idx]}'})
    else:
        return jsonify({'result': 'Intruder detected'})

# ── Run the app (use PORT env var set by Railway) ─────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
