
# ==================================================
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import speech_recognition as sr  # pyright: ignore[reportMissingImports]
import pyttsx3
import datetime
import wikipedia
import pywhatkit
import webbrowser
from threading import Thread, Lock

# ======================================================
# FastAPI setup
# ======================================================
app = FastAPI()  # pyright: ignore[reportUndefinedVariable]

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# Text-to-Speech setup
# ======================================================
# Initialize once with correct Windows driver
import pyttsx3
def speak(text: str):
    """Always speaks the given text — safe for FastAPI & threads."""
    try:
        engine = pyttsx3.init(driverName='sapi5')  # or just pyttsx3.init() if Linux/mac
        engine.setProperty('rate', 170)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"TTS error: {e}")
# ======================================================
#  Speech Recognition setup
# ======================================================
def take_command():
    listener = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎧 Listening...")
        listener.pause_threshold = 1
        audio = listener.listen(source)

    try:
        print("🔍 Recognizing...")
        command = listener.recognize_google(audio, language="en-in")
        command = command.lower()
        print("🗣 You said:", command)
    except Exception:
        return ""

    return command


# ======================================================
#  Input model for commands
# ======================================================
class CommandInput(BaseModel):
    command: str | None = None
    use_mic: bool = False  # added: to use microphone input if True


# ======================================================
#  Command processing endpoint
# ======================================================
@app.post("/voice-command")
def process_command(data: CommandInput):
    """
    POST /voice-command
    - If use_mic=True, listens via microphone.
    - Otherwise, uses command text from frontend.
    """

    # 🎙 If use_mic=True, take voice command
    if data.use_mic:
        speak("Listening now...")
        command = take_command()
    else:
        command = (data.command or "").lower().strip()

    if not command:
        response = "Please say or type something."
        speak(response)
        return {"response": response, "next": ""}
    
    response = "Sorry, I didn't understand that."
    # speak(response)

    # ==================================================
    # 🔧 Command logic
    # ==================================================
    if "hello" in command:
        response = "Hello, how are you?"

    elif "time" in command:
        response = "The time is " + datetime.datetime.now().strftime("%I:%M %p")

    elif "date" in command:
        response = "Today's date is " + datetime.datetime.now().strftime("%d %B, %Y")

    elif "play" in command:
        song = command.replace("play", "").strip()
        response = "Playing " + song
        try:
            pywhatkit.playonyt(song)
        except Exception as e:
            response = "Could not play song: " + str(e)

    elif "wikipedia" in command:
        topic = command.replace("wikipedia", "").strip()
        try:
            response = wikipedia.summary(topic, sentences=2)
        except:
            response = "No Wikipedia result found."

    elif "search" in command:
        query = command.replace("search", "").strip()
        response = "Searching " + query
        try:
            pywhatkit.search(query)
        except:
            response = "Search failed."

    elif "open" in command:
        site = command.replace("open", "").strip()
        url = site if site.startswith("http") else f"https://{site}.com"
        response = "Opening " + site
        try:
            webbrowser.open(url)
        except:
            response = "Failed to open website."

    elif "stop" in command or "exit" in command:
        response = "Goodbye!"
        speak(response)
        return {"response": response, "next": ""}

    # ==================================================
    # 🗣 Speak and return result
    # ==================================================
    speak(response)

    # 🎧 Optional: Wait for next command only if mic mode
    next_cmd = ""
    if data.use_mic:
        next_cmd = take_command()

    return {"heard": command, "response": response, "next": next_cmd}

# uvicorn main:app --reload --port 8000