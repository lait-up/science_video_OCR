import os
import io
import uuid
from werkzeug.utils import secure_filename
import cv2
import pytesseract
import numpy as np
import tempfile
from flask import Flask, request, send_file, render_template, jsonify
from werkzeug.utils import secure_filename
import csv

app = Flask(__name__, static_folder='static')

# UPLOAD_FOLDER = tempfile.mkdtemp()
# 設定上傳目錄為當前專案的 static/videos 目錄
UPLOAD_FOLDER = os.path.join(app.static_folder, 'videos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def extract_numbers_from_video(video_path, regions):
    try:
      cap = cv2.VideoCapture(video_path)
      fps = cap.get(cv2.CAP_PROP_FPS)
      frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
      
      data = []
      frame_interval = int(fps * 0.2)  # 200ms interval
      
      for frame_number in range(0, frame_count, frame_interval):
          cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
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
    except Exception as e:
      print(e)
    return data

# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'code': 200, 'message': 'Test successfully'})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'code': 400, 'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'error': 'No selected file'}), 400
    if file:
        unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        # filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        return jsonify({'code': 200,'message': 'File uploaded successfully', 'filePath': filepath})

@app.route('/process', methods=['POST'])
def process_video_regions():
    try:
        data = request.json
        video_path = data['filePath']
        regions = data['regions']
        result_data = extract_numbers_from_video(video_path, regions)
        return jsonify({'code': 200, 'data': result_data})
    except Exception as e:
        return jsonify({'code': 500, 'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download_csv():
    try:
        data = request.json['tableData']
        # output_file = os.path.join(app.config['UPLOAD_FOLDER'], 'numbers_by_time.csv')
        output = io.StringIO()
        
        # with open(output_file, 'w', newline='') as f:
        #     writer = csv.DictWriter(f, fieldnames=data[0].keys())
        #     writer.writeheader()
        #     writer.writerows(data)
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        # return send_file(output_file, as_attachment=True, download_name='numbers_by_time.csv')
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            as_attachment=True,
            download_name='numbers_by_time.csv',
            mimetype='text/csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_uploaded_files', methods=['POST'])
def delete_uploaded_files():
    data = request.json
    file_paths = data.get('filePaths', [])
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
    
    return jsonify({'message': 'Files deleted successfully', 'code': 200})

if __name__ == '__main__':
    app.run(debug=True)
