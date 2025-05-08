import keyboard  # For typing actions
from pynput import mouse, keyboard as pynput_keyboard  # For listening to mouse clicks and ESC key
import time
import os
import threading

# File where DeepSeek's output (phrases) is expected to be stored
DEEPSEEK_PHRASES_FILENAME = "deepseek_phrases.txt"

phrases = []

# --- Load phrases from DeepSeek's output file ---
try:
    if os.path.exists(DEEPSEEK_PHRASES_FILENAME):
        with open(DEEPSEEK_PHRASES_FILENAME, 'r', encoding='utf-8') as f:
            phrases = [line.strip() for line in f if line.strip()]

        if phrases:
            print(f"Successfully loaded {len(phrases)} phrases from '{DEEPSEEK_PHRASES_FILENAME}'.")
        else:
            print(f"Warning: '{DEEPSEEK_PHRASES_FILENAME}' was found but is empty or contains no valid phrases.")
            print("Please ensure the DeepSeek script ran successfully and generated output.")
    else:
        print(f"Error: '{DEEPSEEK_PHRASES_FILENAME}' not found.")
        print("Please run your DeepSeek script first to generate this file, or place the file in the same directory.")

except Exception as e:
    print(f"An error occurred while trying to read '{DEEPSEEK_PHRASES_FILENAME}': {e}")

if not phrases:
    print("No phrases loaded. Exiting script.")
    exit()

# --- Global state for listeners and main loop ---
current_phrase_index = 0
max_phrases = len(phrases)
typing_allowed = True  # To control typing flow

# Events to signal between threads
click_to_type_event = threading.Event()
quit_script_event = threading.Event()


# --- Mouse Click Listener ---
def on_click(x, y, button, pressed):
    global typing_allowed
    if button == mouse.Button.left and pressed:
        if typing_allowed and not quit_script_event.is_set():
            print("Left click detected!")
            click_to_type_event.set()  # Signal main loop to type
    return not quit_script_event.is_set()  # Stop listener if quit_event is set


# --- Keyboard Listener for ESC ---
def on_key_press(key):
    if key == pynput_keyboard.Key.esc:
        print("ESC key detected, preparing to exit...")
        quit_script_event.set()
        click_to_type_event.set()  # Wake up main loop if it's waiting on click
        return False  # Stop the keyboard listener
    return not quit_script_event.is_set()


# --- Script Execution ---
print("\nYou will have 5 seconds to switch to the target window and click into the input field...")
# MODIFIED: Instructions updated for click
print("After the script starts, LEFT CLICK to type the next phrase, or press ESC to quit.")
time.sleep(5)

print("\n--- Ready to start ---")
print(f"There are a total of {max_phrases} phrases to type.")

# Start listeners
mouse_listener = mouse.Listener(on_click=on_click)
keyboard_listener_for_esc = pynput_keyboard.Listener(on_press=on_key_press)

mouse_listener.start()
keyboard_listener_for_esc.start()

try:
    while current_phrase_index < max_phrases and not quit_script_event.is_set():
        print(
            f"\nClick LEFT MOUSE BUTTON to type phrase ({current_phrase_index + 1}/{max_phrases}), or press ESC to quit.")

        # Wait for a click signal or quit signal
        # Timeout allows the loop to periodically check quit_script_event if click_to_type_event.wait() was blocking indefinitely
        was_signaled = click_to_type_event.wait(timeout=0.5)  # Check every 0.5s

        if quit_script_event.is_set():
            break  # Exit loop if ESC was pressed

        if was_signaled:
            click_to_type_event.clear()  # Reset for the next click

            if current_phrase_index < max_phrases:  # Ensure we don't type if ESC was pressed and index is already max
                typing_allowed = False  # Prevent new clicks from queuing up while typing

                phrase_to_type = phrases[current_phrase_index]
                print(f"  Typing: {phrase_to_type}")

                # Type the phrase (using the 'keyboard' library)
                keyboard.write(phrase_to_type)
                time.sleep(0.05)  # Tiny pause for reliability
                keyboard.press_and_release('enter')

                current_phrase_index += 1
                typing_allowed = True  # Allow next click signal

                if current_phrase_index == max_phrases:
                    print("\nAll phrases have been typed!")
                    quit_script_event.set()  # Signal listeners to stop
                    break
            else:  # Should not happen if logic is correct, but as a safeguard
                break

except KeyboardInterrupt:  # Catch Ctrl+C if pressed in the terminal
    print("\nProgram interruption detected (Ctrl+C), exiting script.")
    quit_script_event.set()
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    quit_script_event.set()
finally:
    print("Script execution finishing...")
    quit_script_event.set()  # Ensure event is set for listeners

    if mouse_listener.is_alive():
        mouse_listener.stop()
        # mouse_listener.join() # Wait for listener thread to finish
    if keyboard_listener_for_esc.is_alive():
        keyboard_listener_for_esc.stop()
        # keyboard_listener_for_esc.join() # Wait for listener thread to finish

    print("Listeners stopped. Script finished.")