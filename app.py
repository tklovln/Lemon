from flask import Flask, render_template, send_from_directory
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    # Your Python code
    title = "Lemon: Emotional LeadSheet Generator"
    return render_template('index.html', title=title)

@app.route('/midis/<path:filename>')
def serve_midi(filename):
    return send_from_directory('midis', filename)

@app.route('/gen_midis/<path:filename>')
def serve_gen_midi(filename):
    return send_from_directory('compose/generation/stage01', filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/generate_leadsheet')
def generate_leadsheet():
    inference_cmd = "python3 stage01_compose/inference.py stage01_compose/config/pop1k7_finetune.yaml generation/stage01 1 4"
    processed_cmd = inference_cmd.split(" ")
    print(processed_cmd)
    subprocess.run(processed_cmd, check=True, cwd="compose")
    output_path = "compose/generation/stage01/samp_01.mid"
    # Assuming the audio file is generated in the current directory with name 'output_audio.wav'
    # return '<a href="/play_audio">Click here to play the generated audio</a>'
    return output_path

@app.route('/')
def refresh_endpoint():
    # Generate or retrieve the refreshed content here
    refreshed_content = "<p>New content goes here</p>"
    return refreshed_content

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')