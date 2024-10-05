from flask import Flask, request, render_template, redirect, url_for
import cv2
import numpy as np
import os
from werkzeug.utils import secure_filename

# Initialize the Flask app
app = Flask(__name__)

# Set up file upload folder
UPLOAD_FOLDER = './uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to process and compare the images (PAN Card vs Template)
def tampering_detection(pan_card_path, template_path):
    # Load images
    pan_card_image = cv2.imread(pan_card_path)
    template_image = cv2.imread(template_path)

    # Convert to grayscale
    pan_card_gray = cv2.cvtColor(pan_card_image, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template_image, cv2.COLOR_BGR2GRAY)

    # Resize template to match the PAN card image size
    template_gray = cv2.resize(template_gray, (pan_card_gray.shape[1], pan_card_gray.shape[0]))

    # Apply Gaussian blur
    pan_card_blur = cv2.GaussianBlur(pan_card_gray, (5, 5), 0)
    template_blur = cv2.GaussianBlur(template_gray, (5, 5), 0)

    # Apply thresholding to create binary images
    _, pan_card_thresh = cv2.threshold(pan_card_blur, 128, 255, cv2.THRESH_BINARY)
    _, template_thresh = cv2.threshold(template_blur, 128, 255, cv2.THRESH_BINARY)

    # Detect differences between the two images
    difference = cv2.absdiff(pan_card_thresh, template_thresh)
    _, tamper_detect = cv2.threshold(difference, 50, 255, cv2.THRESH_BINARY)

    # Save the tampered result image
    result_path = os.path.join(UPLOAD_FOLDER, 'result.png')
    cv2.imwrite(result_path, tamper_detect)

    return result_path

# Define the home route to display the upload form
@app.route('/')
def index():
    return render_template('index.html')

# Define the upload route to handle file upload and tampering detection
@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # Get files from the form
        pan_card_file = request.files['pan_card']
        template_file = request.files['template']
        
        if pan_card_file and allowed_file(pan_card_file.filename) and template_file and allowed_file(template_file.filename):
            pan_filename = secure_filename(pan_card_file.filename)
            template_filename = secure_filename(template_file.filename)
            
            # Save uploaded files to the uploads folder
            pan_path = os.path.join(app.config['UPLOAD_FOLDER'], pan_filename)
            template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_filename)
            pan_card_file.save(pan_path)
            template_file.save(template_path)
            
            # Perform tampering detection
            result_path = tampering_detection(pan_path, template_path)
            
            # Redirect to the result page to display the tampering detection result
            return redirect(url_for('show_result', result_filename='result.png'))
    return redirect(url_for('index'))

# Define the result route to display the tampered image result
@app.route('/result/<result_filename>')
def show_result(result_filename):
    return render_template('result.html', result_image=result_filename)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
