import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from stegon_backend import run_encoding, run_decoding, convert_mp3_to_wav, PYDUB_AVAILABLE


app=Flask(__name__)
app.secret_key= 'mysupersecretkey'

UPLOAD_FOLDER= 'uploads'
OUTPUT_FOLDER= 'outputs'
app.config['UPLOAD_FOLDER']= UPLOAD_FOLDER
app.config['OUTPUT_FOLDER']= OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode_page')
def encode_page():
    return render_template('encode.html')

@app.route('/decode_page')
def decode_page():
    return render_template('decode.html')

@app.route('/encode', methods=['POST'])
def handle_encode():
    message= request.form.get('message')
    audio_file= request.files.get('audio_file')

    if not message:
        flash('Please enter a message to encode.')
        return redirect(url_for('encode_page'))
    if not audio_file:
        flash('Please upload an audio file.')
        return redirect(url_for('encode_page'))
    
    filename= secure_filename(audio_file.filename)
    input_path= os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(input_path)

    temp_wave_path= os.path.join(app.config['UPLOAD_FOLDER'], 'temp_input.wav')
    if filename.lower().endswith('.mp3'):
        if not PYDUB_AVAILABLE:
            flash('MP3 support requires pydub and ffmpeg. Please install them.')
            return redirect(url_for('encode_page'))
        success, msg= convert_mp3_to_wav(input_path, temp_wave_path)
        if not success:
            flash(msg)
            return redirect(url_for('encode_page'))
        audio_to_proccess= temp_wave_path

    else:
        audio_to_proccess= input_path

    output_filename= f'encoded_{filename.rsplit(".",1)[0]}.wav'
    output_path= os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    config={
        'input_file': audio_to_proccess,
        'output_file': output_path,
        'message': message
    }
    result= run_encoding(config)

    if result.get('success'):
        flash('Message encoded successfully!')
        return send_file(result["output_file"], as_attachment=True, download_name=output_filename)
        
    else:
        flash('Failed to encode the message.')
        return redirect(url_for('encode_page'))
    
@app.route('/decode', methods=['POST'])
def handle_decode():
    file= request.files.get('audio_file')
    if not file or file.filename=='':
        return render_template('decode.html', 
                                 message=None, 
                                 error="Error: Please select a file to decode.")
    

    filename= secure_filename(file.filename)
    input_path= os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(input_path)

    config={
        'input_file': input_path
    }

    result= run_decoding(config)

    found_message= None
    error_message= None

    if result.get('success'):
        found_message= result.get('message_found')
    else:
        error_message= result.get('error_message')

    return render_template('decode.html', 
                             message=found_message, 
                             error=error_message)
    
   


if __name__ == '__main__':
    print("Starting Flask server...")
    print(f"pydub available: {PYDUB_AVAILABLE}")
    print("Visit http://127.0.0.1:5000 in your browser.")
    app.run(debug=True)
    