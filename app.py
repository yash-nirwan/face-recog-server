from flask import Flask, request, jsonify
import face_recognition
import os
import io
import base64
import pathlib  # ✅ Added for folder support

# MQTT
import paho.mqtt.publish as publish

# —————————— Telegram imports & config ——————————
import requests

BOT_TOKEN    = "7736035712:AAHFEUAc3mJBLST5G3ffML6VSsVoIkRtNRw"
CHAT_ID      = "6217036575"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_message(text: str):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    try:
        r = requests.post(url, data=payload, timeout=10)
        print("📲 Telegram message:", r.status_code, r.text)
    except Exception as e:
        print("❌ Telegram sendMessage failed:", e)
# ——————————————————————————————————————————————

# Flask app
app = Flask(__name__)

# MQTT broker settings
default_broker = 'test.mosquitto.org'
topic_alert   = 'intruder/alert'
topic_image   = 'yashn1234/intruder/image'

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

# ── Load known faces at startup (supports folders per person) ──
known_encodings = []
known_names     = []

base_path = pathlib.Path("known_faces")
base_path.mkdir(exist_ok=True)

for person_dir in base_path.iterdir():
    if person_dir.is_dir():
        person_name = person_dir.name
        for img_path in person_dir.glob("*.[jp][pn]g"):
            try:
                img = face_recognition.load_image_file(img_path)
                encs = face_recognition.face_encodings(img)
                if encs:
                    known_encodings.append(encs[0])
                    known_names.append(person_name)
                    print(f"✅ Loaded {img_path.name} for '{person_name}'")
                else:
                    print(f"⚠️ No face found in {img_path}")
            except Exception as e:
                print(f"❌ Error loading {img_path}: {e}")

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
    try:
        publish.single(topic_image, payload=b64, hostname=default_broker)
        print(f"📡 Published image to MQTT topic '{topic_image}'")
    except Exception as e:
        print(f"❌ MQTT image publish failed: {e}")

    # Face recognition
    img  = face_recognition.load_image_file(io.BytesIO(data))
    encs = face_recognition.face_encodings(img)
    if not encs:
        result = 'No face detected'
        print(f"❌ {result}")
    else:
        unknown_enc = encs[0]
        face_distances = face_recognition.face_distance(known_encodings, unknown_enc)
        if len(face_distances) > 0:
            best_match_index = face_distances.argmin()
            match_threshold = 0.4  # Adjustable for stricter or looser match
            if face_distances[best_match_index] < match_threshold:
                name = known_names[best_match_index]
                result = f'Face recognized: {name}'
                print(f"✅ {result}")
            else:
                result = 'Intruder detected'
                print(f"❌ {result}")
        else:
            result = 'No known faces loaded'
            print(f"⚠️ {result}")

    # Publish alert result
    try:
        publish.single(topic_alert, payload=result, hostname=default_broker)
        print(f"📡 Published alert to MQTT topic '{topic_alert}': {result}")
    except Exception as e:
        print(f"❌ MQTT alert publish failed: {e}")

    # Telegram alert
    if result.lower().startswith("intruder"):
        send_telegram_message("⚠️ Careful, intruder detected")

    return jsonify({'result': result})

# ── Run Server ───────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
