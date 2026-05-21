
from flask import Flask, render_template, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_tool():

    keyword = request.form['keyword']

    # YOUR LOGIC HERE
    result = f"SEO Result for: {keyword}"

    return result

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
