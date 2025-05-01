from flask import Flask, request, jsonify
import face_recognition
import os
import io
import base64

# MQTT
import paho.mqtt.publish as publish

# Flask app
app = Flask(__name__)

# MQTT broker settings
default_broker = 'test.mosquitto.org'
topic_alert = 'intruder/alert'
topic_image = 'yashn1234/intruder/image'

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
    # Expecting multipart form upload
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

    # Encode to base64 for MQTT
    b64 = base64.b64encode(data).decode('utf8')
    # Publish image payload
    try:
        publish.single(topic_image, payload=b64, hostname=default_broker)
        print(f"📡 Published image to MQTT topic '{topic_image}'")
    except Exception as e:
        print(f"❌ MQTT image publish failed: {e}")

    # Face recognition
    img = face_recognition.load_image_file(io.BytesIO(data))
    encs = face_recognition.face_encodings(img)
    if not encs:
        result = 'No face detected'
        print(f"❌ {result}")
    else:
        matches = face_recognition.compare_faces(known_encodings, encs[0])
        if True in matches:
            name = known_names[matches.index(True)]
            result = f'Face recognized: {name}'
            print(f"✅ {result}")
        else:
            result = 'Intruder detected'
            print(f"❌ {result}")

    # Publish alert result
    try:
        publish.single(topic_alert, payload=result, hostname=default_broker)
        print(f"📡 Published alert to MQTT topic '{topic_alert}': {result}")
    except Exception as e:
        print(f"❌ MQTT alert publish failed: {e}")

    return jsonify({'result': result})

# ── Run Server ───────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)

