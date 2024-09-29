import os
import cv2
import pytesseract
import numpy as np
# import webview
import tempfile
from flask import Flask, request, send_file, render_template, jsonify
from werkzeug.utils import secure_filename
import csv
import threading

app = Flask(__name__)

UPLOAD_FOLDER = tempfile.mkdtemp()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_numbers_from_video(video_path, regions):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    data = []
    
    for frame_number in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break
        
        time = frame_number / fps
        row = {'time': f"{time:.2f}"}
        
        for i, region in enumerate(regions):
            x, y, width, height = map(int, [region['x'], region['y'], region['width'], region['height']])
            roi = frame[y:y+height, x:x+width]
            
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            
            text = pytesseract.image_to_string(thresh, config='--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789')
            
            try:
                number = int(text.strip())
                row[f'Region{i+1}'] = str(number)
            except ValueError:
                row[f'Region{i+1}'] = ''
        
        data.append(row)
    
    cap.release()
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'message': 'File uploaded successfully', 'filepath': filepath})

@app.route('/process', methods=['POST'])
def process_video_regions():
    try:
        data = request.json
        video_path = data['filepath']
        regions = data['regions']
        
        result_data = extract_numbers_from_video(video_path, regions)
        return jsonify(result_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download_csv():
    try:
        data = request.json
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], 'numbers_by_time.csv')
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        return send_file(output_file, as_attachment=True, download_name='numbers_by_time.csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_server():
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # server_thread = threading.Thread(target=start_server)
    # server_thread.daemon = True
    # server_thread.start()
    start_server()
    # webview.create_window('Flask App', 'http://127.0.0.1:5000')
    # webview.start()