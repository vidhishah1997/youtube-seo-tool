from flask import Flask, render_template, request
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/extract', methods=['POST'])
def extract():

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        return "No file selected"

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        uploaded_file.filename
    )

    uploaded_file.save(filepath)

    return f"File uploaded successfully: {uploaded_file.filename}"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
