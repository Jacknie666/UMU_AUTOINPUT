import requests
import json
import os
import whisper  # For advanced speech recognition
from moviepy import AudioFileClip  # For audio extraction

# --- Configuration ---
UMU_QUIZ_URL = 'https://m.umu.cn/napi/v1/quiz/question-list?t=1746703373281&_type=1&element_id=52239758&page=1&size=10'
UMU_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36',
    'referer': 'https://m.umu.cn/session/quiz/result?sessionId=52713745&sKey=3ba0d1af1012e6dfbe565936ba6e5c07&from=session',
    'cookie': 'Hm_lvt_0dda0edb8e4fbece1e49e12fc49614dc=1735974066; Hm_lvt_1adfef4bdd11f6ed014f5b6df6b63302=1735974066; umuU=286b659bcf5e84b7eea3565a6c4563c1; JSESSID=755skrg83668j8a90atkeulu35; estuid=u150259162764; estuidtoken=37fd9f222812f2543ce2eb35191adf411746458452; _lang=zh-cn; c__utmc=1720501571.1403550283; c__utma=1720501571.1403550283.3342535601506082668.1746681897.1746700691.18; c__utmb=1720501571.1403550283.1746700691.1746701452.9'
    # WARNING: This cookie is hardcoded and will expire. Update it if you encounter issues.
}

AUDIO_DOWNLOAD_URL = 'https://statics-umu-cn.umucdn.cn/resource/a/yKG/P5Pit/transcoding/2128248397.mp4'
DOWNLOADED_VIDEO_FILENAME = "downloaded_video.mp4"
WAV_OUTPUT_FILENAME = "audio_for_transcription.wav"
TRANSCRIPTION_TEXT_FILENAME = "transcription_output.txt" # For Whisper's direct transcription
DEEPSEEK_OUTPUT_PHRASES_FILENAME = "deepseek_phrases.txt" # For phrases to be used by keyboard script

DEEPSEEK_API_KEY = "sk-2e3b2878d1a4436db1e7b33a34ce3fb0"  # WARNING: Secure your API key!
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


# --- Function 1: Fetch Quiz Questions ---
def fetch_quiz_questions(url, headers):
    """Fetches quiz questions from the UMU API."""
    print("Fetching quiz questions...")
    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
        print("Successfully fetched data from UMU API.")
        data = response.json()

        if data.get("error_code") == 0 and "data" in data and "list" in data["data"]:
            questions_data = data["data"]["list"]
            extracted_questions = [item["title"] for item in questions_data if "title" in item]
            if not extracted_questions:
                print("No questions found in the API response.")
                return None
            print(f"Successfully extracted {len(extracted_questions)} questions.")
            return extracted_questions
        else:
            print("API returned an error or unexpected data format for quiz questions.")
            print(f"Error Code: {data.get('error_code')}, Message: {data.get('error_message')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"RequestException while fetching quiz questions: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError while parsing quiz questions: {e}")
        print("This might be due to an expired cookie or invalid API response.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching quiz questions: {e}")
        return None


# --- Function 2: Download and Transcribe Audio ---
def download_and_transcribe_audio(audio_url, video_filename, wav_filename, transcription_txt_filename):
    """Downloads, converts, and transcribes audio using Whisper."""
    # Download
    try:
        print(f"Downloading video/audio from {audio_url} to '{video_filename}'...")
        response = requests.get(url=audio_url, headers=UMU_HEADERS, stream=True)
        response.raise_for_status()
        with open(video_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=81920):
                if chunk:
                    f.write(chunk)
        print("Video/audio download successful!")
    except requests.RequestException as e:
        print(f"Request error during video/audio download: {e}")
        return None
    except Exception as e:
        print(f"An unknown error occurred during video/audio download: {e}")
        return None

    # Convert to WAV
    audio_clip = None
    try:
        print(f"Converting '{video_filename}' to '{wav_filename}'...")
        audio_clip = AudioFileClip(video_filename)
        audio_clip.write_audiofile(wav_filename)
        print("Audio extraction to WAV successful!")
    except Exception as e:
        print(f"Error during audio extraction: {e}")
        if audio_clip:
            audio_clip.close() # Ensure closed if opened
        return None
    finally:
        if audio_clip: # Ensure closed if opened
            audio_clip.close()


    # Transcribe using Whisper
    transcription_text = ""
    try:
        print("Loading Whisper model...")
        model_size = "base"
        model = whisper.load_model(model_size)
        print(f"Whisper model '{model_size}' loaded. Starting transcription of '{wav_filename}'...")
        result = model.transcribe(wav_filename, fp16=False)
        transcription_text = result["text"]
        print("\n--- Transcription Result (Whisper) ---")
        print(transcription_text)

        if transcription_text:
            try:
                with open(transcription_txt_filename, 'w', encoding='utf-8') as f:
                    f.write(transcription_text)
                print(f"\nWhisper transcription successfully saved to '{transcription_txt_filename}'")
            except Exception as e:
                print(f"\nError writing Whisper transcription to file: {e}")
        else:
            print("\nNo transcription text from Whisper to save.")
        return transcription_text
    except FileNotFoundError:
        print(f"Error: The audio file '{wav_filename}' was not found for transcription.")
        return None
    except Exception as e:
        print(f"An error occurred during Whisper transcription: {e}")
        return None
    finally:
        print("\nCleaning up temporary audio files used for Whisper...")
        for f_path in [video_filename, wav_filename]:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                    print(f"Removed '{f_path}'.")
                except Exception as e:
                    print(f"Could not remove '{f_path}': {e}")


# --- Function 3: Call DeepSeek API ---
# MODIFIED: Removed prompt_instruction parameter, as instructions are now embedded in user_prompt
def get_deepseek_completion(api_key, questions, transcription):
    """Sends questions and transcription to DeepSeek API and returns the completion."""
    if not questions or not transcription:
        print("DeepSeek: Missing questions or transcription. Skipping API call.")
        return None

    print("\nPreparing data for DeepSeek API...")
    formatted_questions = "\n".join([f"{q}" for q in questions]) # Simpler formatting for questions if numbering is not desired in prompt

    # MODIFIED: User prompt refined for specific output format
    user_prompt = f"""Given the following audio transcription and questions:

Audio Transcription:
---
{transcription}
---

Questions:
{formatted_questions}

Your task is to use the information from the audio transcription to answer the questions or fill in any blanks (e.g., "_______").

Instructions for your output:
1. Provide only the completed sentences or direct answers based on the questions and transcription.
2. Each completed sentence or answer must be on a new line.
3. Do NOT include any numbering (like "1.", "2."), bullet points, or any other introductory/explanatory text (e.g., "Here are the answers:") in your response. 
4. Output only the answer phrases themselves, ensuring each phrase intended for typing starts on a new line.

For example, if a question is "The capital of France is ____." and the transcription mentions Paris, your output for that line should be:
The capital of France is Paris.
If a question is "Describe the weather." and the transcription says "It is sunny.", your output for that line should be:
It is sunny.
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an assistant that provides concise answers based on given context and questions, formatted as a list of phrases, each on a new line."},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.5, # Adjusted for more factual/direct answers
        "max_tokens": 1500
    }

    print("Sending request to DeepSeek API...")
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        api_response_data = response.json()

        if api_response_data.get("choices") and len(api_response_data["choices"]) > 0:
            deepseek_result = api_response_data["choices"][0].get("message", {}).get("content", "")
            if deepseek_result:
                print("Successfully received response from DeepSeek.")
                return deepseek_result.strip() # .strip() to remove leading/trailing newlines from the whole block
            else:
                print("DeepSeek API response did not contain the expected content.")
                print("Full API Response:", api_response_data)
                return None
        else:
            print("DeepSeek API response format not as expected.")
            print("Full API Response:", api_response_data)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error calling DeepSeek API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"DeepSeek API Error Response: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"DeepSeek API Error Response (not JSON): {e.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred with DeepSeek API call: {e}")
        return None


# --- Main Execution ---
if __name__ == "__main__":
    print("--- Starting Script ---")

    quiz_questions = fetch_quiz_questions(UMU_QUIZ_URL, UMU_HEADERS)
    if not quiz_questions:
        print("Could not retrieve quiz questions. Further processing that depends on questions might be affected.")
        quiz_questions = [] # Continue with empty list if needed, or handle differently

    audio_transcription = download_and_transcribe_audio(
        AUDIO_DOWNLOAD_URL,
        DOWNLOADED_VIDEO_FILENAME,
        WAV_OUTPUT_FILENAME,
        TRANSCRIPTION_TEXT_FILENAME
    )
    if not audio_transcription:
        print("Could not retrieve audio transcription. Further processing that depends on transcription might be affected.")
        # audio_transcription will be None or empty

    if quiz_questions and audio_transcription:
        # MODIFIED: prompt_instruction is now part of the refined user_prompt within get_deepseek_completion
        deepseek_output = get_deepseek_completion(
            DEEPSEEK_API_KEY,
            quiz_questions,
            audio_transcription
        )

        if deepseek_output:
            print("\n\n--- DeepSeek API Result (Raw) ---")
            print(deepseek_output)

            # --- ADDED: Save DeepSeek output to a file for the keyboard script ---
            try:
                with open(DEEPSEEK_OUTPUT_PHRASES_FILENAME, "w", encoding="utf-8") as f:
                    # Ensure each phrase is on a new line if DeepSeek returns a single block.
                    # The .strip() on deepseek_output in get_deepseek_completion helps,
                    # and the prompt asks for newline-separated phrases.
                    f.write(deepseek_output)
                print(f"\nDeepSeek output successfully saved to '{DEEPSEEK_OUTPUT_PHRASES_FILENAME}' for keyboard script.")
            except Exception as e:
                print(f"\nError saving DeepSeek output to '{DEEPSEEK_OUTPUT_PHRASES_FILENAME}': {e}")
            # --- END ADDED ---
        else:
            print("\nFailed to get a valid result from DeepSeek API.")
    elif not quiz_questions:
        print("\nSkipping DeepSeek API call because quiz questions could not be fetched.")
    elif not audio_transcription: # This condition might be met if quiz_questions also failed.
        print("\nSkipping DeepSeek API call because audio transcription could not be generated.")

    print("\n--- Script Finished ---")