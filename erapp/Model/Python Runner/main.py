from keras.models import load_model
from time import sleep
from keras.preprocessing.image import img_to_array
from keras.preprocessing import image
import cv2
import numpy as np
from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS

# Get the absolute path to the current script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Update the model path to use the absolute path
model_path = os.path.join(script_dir, 'model.h5')
classifier = load_model(model_path)

face_classifier = cv2.CascadeClassifier(os.path.join(script_dir, 'haarcascade_frontalface_default.xml'))

emotion_labels = ['Angry','Disgust','Fear','Happy','Neutral', 'Sad', 'Surprise']

# Initialize Flask app
app = Flask(__name__)
# Enable CORS with specific configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configure upload folder
UPLOAD_FOLDER = os.path.join(script_dir, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/detect_emotion', methods=['POST', 'OPTIONS'])
def detect_emotion():
    if request.method == 'OPTIONS':
        # Respond to preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read and process the image
        frame = cv2.imread(filepath)
        if frame is None:
            return jsonify({'error': 'Could not read image'}), 400
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray)
        
        if len(faces) == 0:
            return jsonify({'error': 'No face detected'}), 400
            
        # Process the first face found
        x, y, w, h = faces[0]
        roi_gray = gray[y:y+h, x:x+w]
        roi_gray = cv2.resize(roi_gray, (48, 48), interpolation=cv2.INTER_AREA)
        
        if np.sum([roi_gray]) != 0:
            roi = roi_gray.astype('float') / 255.0
            roi = img_to_array(roi)
            roi = np.expand_dims(roi, axis=0)
            
            prediction = classifier.predict(roi)[0]
            max_index = prediction.argmax()
            emotion = emotion_labels[max_index]
            confidence = float(prediction[max_index])
            
            # Clean up the uploaded file
            os.remove(filepath)
            
            response = jsonify({
                'emotion': emotion,
                'confidence': confidence
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        else:
            return jsonify({'error': 'Could not process face'}), 400
            
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Make sure to install flask-cors: pip install flask-cors
    app.run(host='0.0.0.0', port=5000, debug=True)