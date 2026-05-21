from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/extract', methods=['POST'])
def extract():

    youtube_url = request.form.get('youtube_url')

    if not youtube_url:
        return "No YouTube URL entered"

    return f"""
    <h1>Extraction Started</h1>

    <p><strong>You entered:</strong></p>

    <p>{youtube_url}</p>
    """


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
