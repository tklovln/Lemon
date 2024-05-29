from flask import Flask, render_template, send_from_directory, jsonify
import subprocess
import json, os
import shutil

app = Flask(__name__)
midi_id = "000"

def read_json(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

def write_json(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file)

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
    return send_from_directory(f'compose/generation/{midi_id}', filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/delete_directory/<path:directory>', methods=['DELETE'])
def delete_directory(directory):
    print(f"delete: {directory}")
    try:
        shutil.rmtree(directory)
        return f'Directory {directory} deleted successfully', 200
    except Exception as e:
        return f'Error deleting directory {directory}: {str(e)}', 500
    

@app.route('/generate_leadsheet')
def generate_leadsheet():
    inference_cmd = f"python3 stage01_compose/inference.py stage01_compose/config/pop1k7_finetune.yaml generation/{midi_id} 1 16"
    processed_cmd = inference_cmd.split(" ")
    print(processed_cmd)
    subprocess.run(processed_cmd, check=True, cwd="compose")
    output_path = f"compose/generation/{midi_id}/samp_01.mid"
    return output_path

@app.route('/logger')
def logger():
    file_path = f"compose/generation/{midi_id}/log.json"
    if not os.path.exists(file_path):
        return jsonify({'progress':0})
    data = read_json(file_path)
    return data  # Example progress value

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    