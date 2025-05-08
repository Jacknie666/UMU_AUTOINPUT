import requests
import os
import whisper # For advanced speech recognition

# --- Part 1: Download audio file (as per your original script) ---
url = 'https://statics-umu-cn.umucdn.cn/resource/a/yKG/J9b5o/transcoding/2388061351.mp3'
headers = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36',
    'referer': 'https://m.umu.cn/',
}
mp3_input_filename = "video.mp3"
wav_output_filename = "audio.wav"
transcription_output_filename = "transcription_output.txt" # File to save the transcription

try:
    print(f"Downloading '{mp3_input_filename}'...")
    # Note: If you encounter proxy errors again, you might need the proxies={'http':None, 'https':None} fix
    response = requests.get(url=url, headers=headers, stream=True)
    response.raise_for_status()

    with open(mp3_input_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print("File download successful!")
except requests.RequestException as e:
    print(f"Request error during download: {e}")
    exit()
except Exception as e:
    print(f"An unknown error occurred during download: {e}")
    exit()

# --- Part 2: Extract audio to WAV (as per your original script) ---
from moviepy import AudioFileClip

try:
    print(f"Converting '{mp3_input_filename}' to '{wav_output_filename}'...")
    audio_clip = AudioFileClip(mp3_input_filename)
    audio_clip.write_audiofile(wav_output_filename)
    print("Audio extraction to WAV successful!")
except Exception as e:
    print(f"Error during audio extraction: {e}")
    if 'audio_clip' in locals():
        audio_clip.close()
    exit()
finally:
    if 'audio_clip' in locals() and hasattr(audio_clip, 'close') and callable(audio_clip.close):
        audio_clip.close()

# --- Part 3: Improved Audio Recognition with OpenAI Whisper ---
transcription_text = ""
try:
    print("Loading Whisper model...")
    model_size = "base" # Change as needed: "tiny", "base", "small", "medium", "large"
    model = whisper.load_model(model_size)
    print(f"Whisper model '{model_size}' loaded. Starting transcription of '{wav_output_filename}'...")

    result = model.transcribe(wav_output_filename, fp16=False) # fp16=False for CPU stability
    transcription_text = result["text"]

    print("\n--- Transcription Result ---")
    print(transcription_text)

    # --- ADDED: Write transcription to a file ---
    if transcription_text: # Only write if there's something to write
        try:
            with open(transcription_output_filename, 'w', encoding='utf-8') as f:
                f.write(transcription_text)
            print(f"\nTranscription successfully saved to '{transcription_output_filename}'")
        except Exception as e:
            print(f"\nError writing transcription to file '{transcription_output_filename}': {e}")
    else:
        print("\nNo transcription text to save.")
    # --- END ADDED FEATURE ---

except FileNotFoundError:
    print(f"Error: The audio file '{wav_output_filename}' was not found for transcription.")
except Exception as e:
    print(f"An error occurred during Whisper transcription: {e}")

# --- Part 4: Cleanup (Optional but recommended) ---
finally:
    print("\nCleaning up temporary input files...")
    try:
        if os.path.exists(mp3_input_filename):
            os.remove(mp3_input_filename)
            print(f"Removed '{mp3_input_filename}'.")
        if os.path.exists(wav_output_filename):
            os.remove(wav_output_filename)
            print(f"Removed '{wav_output_filename}'.")
    except Exception as e:
        print(f"Error during cleanup: {e}")