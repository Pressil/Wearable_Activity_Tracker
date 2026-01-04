from flask import Flask, request, jsonify
import joblib
import numpy as np
import datetime
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

LABEL_MAP = {0: "Walking", 1: "Running"}
last_saved_activity = None
last_history_time = datetime.datetime.now()

try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://wearable-activity-tracke-a5c56-default-rtdb.firebaseio.com/' 
    })
    print("✓ Firebase Connected")
except Exception as e:
    print("✗ Firebase Error:", e)

try:
    model = joblib.load('activity_model.pkl')
    print("✓ ML Model Loaded")
except Exception as e:
    print("✗ Model Error:", e)

def extract_features(data_list):
    try:
        ax = [float(item['ax']) for item in data_list]
        ay = [float(item['ay']) for item in data_list]
        az = [float(item['az']) for item in data_list]
        gx = [float(item['gx']) for item in data_list]
        gy = [float(item['gy']) for item in data_list]
        gz = [float(item['gz']) for item in data_list]

        movement_check = np.std(ax) + np.std(ay) + np.std(az)
        
        if movement_check < 300: 
            return None

        features = [
            float(np.mean(ax)), float(np.std(ax)),
            float(np.mean(ay)), float(np.std(ay)),
            float(np.mean(az)), float(np.std(az)),
            float(np.mean(gx)), float(np.std(gx)),
            float(np.mean(gy)), float(np.std(gy)),
            float(np.mean(gz)), float(np.std(gz)),
        ]
        return np.array([features], dtype=float)
    except:
        return None

def sync_to_firebase(activity_name, timestamp, confidence):
    global last_saved_activity, last_history_time
    try:
        db.reference('current_reading').set({
            'activity': activity_name,
            'confidence': float(confidence),
            'timestamp': timestamp
        })

        now_time = datetime.datetime.now()
        if activity_name != last_saved_activity or (now_time - last_history_time).total_seconds() > 10:
            db.reference('history').push({'activity': activity_name, 'timestamp': timestamp})
            last_saved_activity = activity_name
            last_history_time = now_time
    except Exception as e:
        print("Firebase Sync Error:", e)

@app.route('/readings', methods=['POST'])
def receive_readings():
    try:
        body = request.get_json(force=True)
        data = body['readings']
        now = datetime.datetime.now().strftime("%H:%M:%S")

        mags = [np.sqrt(float(i['ax'])**2 + float(i['ay'])**2 + float(i['az'])**2) for i in data]
        avg_mag = np.mean(mags)

        features = extract_features(data)
        
        if features is None or avg_mag < 1300:
            activity_name = "Stationary"
            conf = 100.0 - (avg_mag / 30.0) 
        else:
            probs = model.predict_proba(features)[0]
            ai_idx = np.argmax(probs)
            ai_label = LABEL_MAP.get(int(ai_idx), "Stationary")
            raw_ai_conf = float(probs[ai_idx] * 100)

            if ai_label == "Running" and avg_mag > 6500:
                activity_name = "Running"
                conf = raw_ai_conf
            
            else:
                activity_name = "Walking"
            
                if ai_label == "Walking":
                    conf = raw_ai_conf
                else:
                    conf = 75.0 + (avg_mag / 200.0) 

        final_conf = round(max(min(conf, 99.85), 0.0), 2) 

        sync_to_firebase(activity_name, now, final_conf)
        print(f"[{now}] Energy: {int(avg_mag)} | Label: {activity_name} | Conf: {final_conf}%")

        return jsonify({"status": "success", "prediction": activity_name, "confidence": final_conf})

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)