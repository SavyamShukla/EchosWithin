import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import wave
import os



#import pydub for converting mp3 to wav
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Warning: 'pydub' library not found. MP3 conversion will be disabled.")
    print("To enable it, run: pip install pydub")
    print("You also need FFmpeg installed on your system.")


# stengnography backend

def convert_mp3_to_wav(mp3_path, wav_path):
    """ Converts an .mp3 file to a .wav file. """
    if not PYDUB_AVAILABLE:
        return False, "pydub library is not installed."
        
    print(f"Converting '{mp3_path}' to '{wav_path}'...")
    try:
        sound = AudioSegment.from_mp3(mp3_path)
        sound.export(wav_path, format="wav")
        print("Conversion successful!")
        return True, "Conversion successful"
    except FileNotFoundError:
        return False, f"Error: The file '{mp3_path}' was not found."
    except Exception as e:
        error_message = (
            f"An error occurred: {e}\n\n"
            "*** IMPORTANT ***\n"
            "Please ensure FFmpeg is installed and in your system's PATH.\n"
            "You can download it from https://ffmpeg.org/download.html"
        )
        return False, error_message

def message_to_bits(message, delimiter="###END###"):
    message_bytes = message.encode("utf-8") + delimiter.encode("utf-8")
    bit_list = [format(byte, '08b') for byte in message_bytes]
    return "".join(bit_list)

def bytes_to_bits(byte_data):
    extracted_bits_list = [str(byte & 1) for byte in byte_data]
    return "".join(extracted_bits_list)

def bits_to_message(bit_string, delimiter="###END###"):
    extracted_bytes = b""
    for i in range(0, len(bit_string), 8):
        byte_string = bit_string[i:i+8]
        if len(byte_string) < 8:
            break
        byte_value = int(byte_string, 2)
        extracted_bytes += byte_value.to_bytes(1, 'big')
        try:
            if delimiter in extracted_bytes.decode("utf-8", errors="ignore"):
                break
        except:
            pass
    try:
        full_message = extracted_bytes.decode("utf-8")
        delimiter_index = full_message.find(delimiter)
        return full_message[:delimiter_index] if delimiter_index != -1 else None
    except UnicodeDecodeError:
        return None

def run_encoding(config):
    input_file = config["input_file"]
    output_file = config["output_file"]
    message = config["message"]

    if not os.path.exists(input_file):
        return {"success": False, "error": f"File not found: {input_file}"}

    try:
        with wave.open(input_file, mode='rb') as song:
            n_frames = song.getnframes()
            frames = song.readframes(n_frames)
            params = song.getparams()
        frame_bytes = bytearray(frames)
    except Exception as e:
        return {"success": False, "error": f"Error reading WAV file: {e}"}

    message_bits = message_to_bits(message)
    num_bits = len(message_bits)

    if num_bits > len(frame_bytes):
        return {"success": False, "error": "Message is too long for this file."}

    for i in range(num_bits):
        bit_to_hide = int(message_bits[i])
        current_byte = frame_bytes[i]
        
        if bit_to_hide == 1:
            frame_bytes[i] = current_byte | 1
        else:
            frame_bytes[i] = current_byte & 254
            
    try:
        with wave.open(output_file, 'wb') as new_song:
            new_song.setparams(params)
            new_song.writeframes(frame_bytes)
    except Exception as e:
        return {"success": False, "error": f"Error writing new WAV file: {e}"}

    return {"success": True, "output_file": output_file}

def run_decoding(config):
    input_file = config["input_file"]
    if not os.path.exists(input_file):
        return {"success": False, "error": f"File not found: {input_file}"}
        
    try:
        with wave.open(input_file, mode='rb') as song:
            frames = song.readframes(song.getnframes())
    except Exception as e:
        return {"success": False, "error": f"Error reading WAV file: {e}\nIs it a valid .wav file?"}

    extracted_bits = bytes_to_bits(frames)
    secret_message = bits_to_message(extracted_bits)
    
    if secret_message is not None:
        return {"success": True, "message_found": secret_message}
    else:
        return {"success": False, "error": "No message found or data was corrupt."}


