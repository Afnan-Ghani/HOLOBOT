from flask import Flask, request, jsonify
from flask_cors import CORS
import serial

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Connect to Arduino on correct port
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

@app.route('/pantilt', methods=['POST', 'OPTIONS'])
def pantilt():
    if request.method == 'OPTIONS':
        response = jsonify({'ok': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    data = request.get_json(force=True)
    pan  = int(data.get('pan',  0))
    tilt = int(data.get('tilt', 0))

    # Map -100..100 → 0..180 degrees
    pan_angle  = 90 + int(pan  * 0.9)
    tilt_angle = 90 + int(tilt * 0.9)

    cmd = f"P{pan_angle}T{tilt_angle}\n"
    ser.write(cmd.encode())
    print(f"[pantilt] pan={pan} tilt={tilt} → {cmd.strip()}")

    response = jsonify({'ok': True})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

if __name__ == '__main__':
    print("Pan-Tilt server starting on http://0.0.0.0:8080")
    print("Set endpoint in UI to: http://192.168.137.70:8080/pantilt")
    app.run(host='0.0.0.0', port=8080, debug=False)
