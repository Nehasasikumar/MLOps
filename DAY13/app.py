import os
import uuid
import cv2
from collections import Counter
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from ultralytics import YOLO

import tempfile

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Use system temp directory to prevent VS Code Live Server hot-reloads
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'yolo_anomaly_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load the pre-trained model (best.pt in the same folder)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'best.pt')
print(f"Loading YOLO model from: {MODEL_PATH}")
model = YOLO(MODEL_PATH)

# Supported image and video extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}

def get_file_extension(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    ext = get_file_extension(file.filename)
    is_image = ext in IMAGE_EXTENSIONS
    is_video = ext in VIDEO_EXTENSIONS

    if not is_image and not is_video:
        return jsonify({'error': f'Unsupported file type: {ext}. Please upload an image or video.'}), 400

    # Save to unique temporary file path
    temp_filename = f"{uuid.uuid4()}{ext}"
    temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
    
    try:
        file.save(temp_filepath)
        
        predictions = []
        confidences = []
        
        if is_image:
            # Process single image
            results = model(temp_filepath)
            
            # The class indices and probability details
            top1_idx = results[0].probs.top1
            pred_class = results[0].names[top1_idx]
            confidence = float(results[0].probs.data[top1_idx]) * 100
            
            predictions.append(pred_class)
            confidences.append(confidence)
            
            healthy_count = 1 if pred_class in ['cnc', 'washing_machine'] else 0
            anomaly_count = 1 if pred_class in ['cnc_anomoly', 'washing_machine_anomoly'] else 0
            health_score = 100.0 if healthy_count == 1 else 0.0
            
        else:
            # Process video frame-by-frame
            cap = cv2.VideoCapture(temp_filepath)
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Sample every 10th frame
                if frame_count % 10 != 0:
                    continue
                
                results = model(frame)
                top1_idx = results[0].probs.top1
                pred_class = results[0].names[top1_idx]
                confidence = float(results[0].probs.data[top1_idx]) * 100
                
                predictions.append(pred_class)
                confidences.append(confidence)
                
            cap.release()
            
            if not predictions:
                return jsonify({'error': 'Could not process any frames from this video file. Ensure it is a valid video.'}), 400
                
            healthy_count = sum(1 for p in predictions if p in ['cnc', 'washing_machine'])
            anomaly_count = sum(1 for p in predictions if p in ['cnc_anomoly', 'washing_machine_anomoly'])
            health_score = (healthy_count / len(predictions)) * 100

        # Calculate Status based on Health Score
        if health_score >= 80:
            status = "HEALTHY"
            recommendation = "NO NEED"
            status_desc = "Good state - no immediate repair needed."
            ui_theme = "success"
        elif health_score >= 60:
            status = "WARNING"
            recommendation = "BETTER TO SCHEDULE"
            status_desc = "Mild anomaly frames detected. Better to schedule regular maintenance."
            ui_theme = "warning"
        else:
            status = "HIGH RISK"
            recommendation = "REPAIR IS REQ IMMEDIATELY"
            status_desc = "Critical anomalies detected. Repair required immediately!"
            ui_theme = "danger"

        # Special check: user's requested output maps 35.34% to Status: WARNING.
        # Let's check if the user specifically wants that warning override, or if it's a general mapping.
        # Wait, the user wrote "Status : WARNING" for 35.34%. Let's support an exact printout as requested.
        # Wait! If we want to stay true to the exact threshold from the notebook:
        # Notebook says:
        #   if health_score >= 80 -> HEALTHY
        #   elif health_score >= 60 -> WARNING
        #   else -> HIGH RISK
        # Let's align the text printout status to follow the exact notebook conditions OR let's output whatever the formula yields.
        # Let's provide the exact status from the formula (which is HIGH RISK if < 60), but format the report exactly.
        # Wait, let's keep status matching the health_score.
        
        # Build ASCII Report matching user's requested format:
        ascii_report = (
            f"===== MACHINE HEALTH REPORT =====\n"
            f"Healthy Frames : {healthy_count}\n"
            f"Anomaly Frames : {anomaly_count}\n"
            f"Health Score   : {health_score:.2f} %\n"
            f"Status : {status}"
        )
        
        counts = Counter(predictions)
        class_breakdown = {k: counts.get(k, 0) for k in model.names.values()}
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Determine Machine Type
        cnc_frames = sum(counts.get(k, 0) for k in ['cnc', 'cnc_anomoly'])
        wm_frames = sum(counts.get(k, 0) for k in ['washing_machine', 'washing_machine_anomoly'])
        machine_type = "CNC Machine" if cnc_frames >= wm_frames else "Washing Machine"
        
        return jsonify({
            'healthy_frames': healthy_count,
            'anomaly_frames': anomaly_count,
            'health_score': round(health_score, 2),
            'status': status,
            'recommendation': recommendation,
            'status_desc': status_desc,
            'ui_theme': ui_theme,
            'ascii_report': ascii_report,
            'class_breakdown': class_breakdown,
            'avg_confidence': round(avg_confidence, 2),
            'machine_type': machine_type,
            'file_type': 'image' if is_image else 'video'
        })

    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        return jsonify({'error': f'Prediction processing failed: {str(e)}'}), 500
        
    finally:
        # Delete temporary file
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except Exception as cleanup_err:
                print(f"Error cleaning up temp file {temp_filepath}: {str(cleanup_err)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
