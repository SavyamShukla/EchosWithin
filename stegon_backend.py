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

# --- GUI Application Class ---

class StegApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Steganography Tool")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # Style
        style = ttk.Style(self)
        style.configure('TButton', padding=5, font=('Helvetica', 10))
        style.configure('TLabel', padding=5, font=('Helvetica', 10))
        style.configure('TEntry', padding=5)

        # Tabs
        self.notebook = ttk.Notebook(self)
        self.encode_tab = ttk.Frame(self.notebook, padding=10)
        self.decode_tab = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.encode_tab, text='Encode Message')
        self.notebook.add(self.decode_tab, text='Decode Message')
        self.notebook.pack(expand=True, fill='both')
        
        # --- Build Tabs ---
        self.create_encode_widgets()
        self.create_decode_widgets()
        
    def create_encode_widgets(self):
        frame = self.encode_tab
        
        # --- Input File ---
        ttk.Label(frame, text="Input Song (.mp3 or .wav):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.encode_in_path = tk.StringVar()
        ttk.Entry(frame, textvariable=self.encode_in_path, width=40).grid(row=1, column=0, padx=5)
        ttk.Button(frame, text="Browse...", command=self.select_encode_input).grid(row=1, column=1, padx=5)
        
        # --- Output File ---
        ttk.Label(frame, text="Output File (.wav):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.encode_out_path = tk.StringVar()
        ttk.Entry(frame, textvariable=self.encode_out_path, width=40).grid(row=3, column=0, padx=5)
        ttk.Button(frame, text="Save As...", command=self.select_encode_output).grid(row=3, column=1, padx=5)
        
        # --- Secret Message ---
        ttk.Label(frame, text="Secret Message:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.secret_message_text = scrolledtext.ScrolledText(frame, height=8, width=58, wrap=tk.WORD)
        self.secret_message_text.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        
        # --- Encode Button ---
        ttk.Button(frame, text="Encode Message", command=self.handle_encode).grid(row=6, column=0, columnspan=2, pady=15)

    def create_decode_widgets(self):
        frame = self.decode_tab
        
        # --- Input File ---
        ttk.Label(frame, text="Input File with Secret (.wav):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.decode_in_path = tk.StringVar()
        ttk.Entry(frame, textvariable=self.decode_in_path, width=40).grid(row=1, column=0, padx=5)
        ttk.Button(frame, text="Browse...", command=self.select_decode_input).grid(row=1, column=1, padx=5)

        # --- Decode Button ---
        ttk.Button(frame, text="Decode Message", command=self.handle_decode).grid(row=2, column=0, columnspan=2, pady=15)

        # --- Decoded Message ---
        ttk.Label(frame, text="Decoded Message:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.decoded_message_text = scrolledtext.ScrolledText(frame, height=10, width=58, wrap=tk.WORD, state='disabled')
        self.decoded_message_text.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

    # --- File Dialog Functions ---
    def select_encode_input(self):
        filetypes = [("Audio Files", ".mp3 .wav"), ("All Files", "*.*")]
        path = filedialog.askopenfilename(title="Select Input Song", filetypes=filetypes)
        if path:
            self.encode_in_path.set(path)

    def select_encode_output(self):
        filetypes = [("WAV Files", ".wav"), ("All Files", "*.*")]
        path = filedialog.asksaveasfilename(title="Save Secret File As", filetypes=filetypes, defaultextension=".wav")
        if path:
            self.encode_out_path.set(path)
            
    def select_decode_input(self):
        filetypes = [("WAV Files", ".wav"), ("All Files", "*.*")]
        path = filedialog.askopenfilename(title="Select Secret File", filetypes=filetypes)
        if path:
            self.decode_in_path.set(path)

    # --- Button Handler Functions ---
    def handle_encode(self):
        in_path = self.encode_in_path.get()
        out_path = self.encode_out_path.get()
        message = self.secret_message_text.get("1.0", tk.END).strip()
        
        if not in_path or not out_path or not message:
            messagebox.showwarning("Warning", "Please fill in all fields.")
            return

        temp_wav = None # To track if we make a temp file
        
        # Check if we need to convert MP3
        if in_path.lower().endswith(".mp3"):
            if not PYDUB_AVAILABLE:
                messagebox.showerror("Error", "pydub library is needed to convert .mp3 files.")
                return
            
            temp_wav = "temp_conversion.wav" # Name for our temporary file
            
            # --- Call the conversion function ---
            success, msg = convert_mp3_to_wav(in_path, temp_wav)
            if not success:
                messagebox.showerror("MP3 Conversion Failed", msg)
                return
            
            # Use the new temp file as the input for encoding
            input_for_encoding = temp_wav
        else:
            # It's already a .wav, use it directly
            input_for_encoding = in_path

        # --- Run the encoding ---
        config = {
            "input_file": input_for_encoding,
            "output_file": out_path,
            "message": message
        }
        report = run_encoding(config)
        
        # --- Clean up the temporary file if we made one ---
        if temp_wav and os.path.exists(temp_wav):
            os.remove(temp_wav)
            print(f"Removed temporary file: {temp_wav}")
        
        # --- Show final report ---
        if report["success"]:
            messagebox.showinfo("Success", f"Message hidden successfully in:\n{report['output_file']}")
        else:
            messagebox.showerror("Error", f"Encoding failed:\n{report['error']}")

    def handle_decode(self):
        in_path = self.decode_in_path.get()
        
        if not in_path:
            messagebox.showwarning("Warning", "Please select an input file.")
            return

        if not in_path.lower().endswith(".wav"):
            messagebox.showwarning("Warning", "Please select a .wav file to decode.")
            return

        config = {"input_file": in_path}
        report = run_decoding(config)

        # Clear the text box and enable it
        self.decoded_message_text.config(state='normal')
        self.decoded_message_text.delete("1.0", tk.END)
        
        if report["success"]:
            self.decoded_message_text.insert("1.0", report['message_found'])
            messagebox.showinfo("Success", "Message decoded!")
        else:
            self.decoded_message_text.insert("1.0", f"--- ERROR ---\n{report['error']}")
            messagebox.showerror("Error", f"Decoding failed:\n{report['error']}")
            
        # Disable the text box so user can't type in it
        self.decoded_message_text.config(state='disabled')

# --- Main execution ---
if __name__ == "__main__":
    app = StegApp()
    app.mainloop()