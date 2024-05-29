from flask import Flask, render_template, send_from_directory
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    # Your Python code
    result = "Lemon: Emotional LeadSheet Generator"
    return render_template('index.html', result=result)

@app.route('/midis/<path:filename>')
def serve_midi(filename):
    return send_from_directory('midis', filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')