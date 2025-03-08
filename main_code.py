import streamlit as st
import speech_recognition as sr
from datetime import datetime
import os
import whisper
import vosk
import wave

# Load the Whisper model
whisper_model = whisper.load_model("base")  # Options: "tiny", "small", "medium", "large"

apis = {"Google Speech Recognition": "google", "Vosk (Offline)": "vosk"}
languages = {"English": "en-US", "French": "fr-FR", "Spanish": "es-ES"}
FILE_NAME = "script.txt"
r = sr.Recognizer()
vosk_model = vosk.Model("./models/vosk-model-small-fr-0.22")  
def transcribe_speech(api, language):
    """Captures and transcribes speech from the microphone using the selected API."""
    with sr.Microphone() as source:
        st.info("Speak now...") 
        r.adjust_for_ambient_noise(source)  

        try:
            audio_text = r.listen(source) 
            st.info("Transcribing...")  

            if api == "google":
                text = r.recognize_google(audio_text, language=language)
            elif api == "vosk":
                text = transcribe_with_vosk(audio_text)
            else:
                text = "The API is not working."

            return text  

        except sr.UnknownValueError:
            return "Could not understand audio"  
        except sr.RequestError as e:
            return "API request error: " + str(e)
        except sr.WaitTimeoutError:
            return "Timeout error"

def transcribe_with_vosk(audio_text):
    """Transcribes audio using Vosk offline."""
    try:
        # Convert the audio to WAV format since Vosk works with WAV files
        with wave.open(audio_text, "rb") as wf:
            rec = vosk.KaldiRecognizer(vosk_model, wf.getframerate())
            data = wf.readframes(wf.getnframes())
            if rec.AcceptWaveform(data):
                result = rec.Result()
                return result
            else:
                return "Could not transcribe using Vosk."
    except Exception as e:
        return f"Error with Vosk: {str(e)}"

def transcribe_audio_file(audio_file):
    """Transcribes an uploaded audio file using Whisper."""
    try:
        st.info("Transcribing file... Please wait!")
        result = whisper_model.transcribe(audio_file)
        text = result["text"] if "text" in result else "No transcription result."
        return text
    except Exception as e:
        return f"Error processing file: {str(e)}"

def save_transcription(text):
    """Saves the transcribed text to a file with a timestamp."""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        with open(FILE_NAME, "a", encoding="utf-8") as f:
            f.write(f"\n[{now}]\n{text}\n{'-'*40}\n")
        st.success(f"Transcription saved to {FILE_NAME}")  
    except Exception as e:
        st.error(f"Error saving file: {e}")  

def load_file():
    """Loads transcription file content if it exists."""
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def save_file(content):
    """Saves modified content to the transcription file."""
    try:
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write(content)
        st.sidebar.success("Modifications saved!")  
    except Exception as e:
        st.sidebar.error(f"Error saving file: {e}")  

def main():
    # Streamlit App
    st.set_page_config(page_title="Speech Recognition App", layout="wide")  
    st.title("🎙️ Speech Recognition App")  

    # Sidebar Navigation
    page = st.sidebar.radio("Choose Mode:", ["🎤 Live Speech", "📂 Upload Audio"])

    # Sidebar for File Editing
    st.sidebar.title("📝 Modify Transcriptions")
    file_content = load_file()  
    edited_content = st.sidebar.text_area("Edit your transcriptions:", file_content, height=300)

    if st.sidebar.button("Save Changes"):
        save_file(edited_content)

    if page == "🎤 Live Speech":
        st.write("Click on the microphone to start speaking:")
        api = st.selectbox("🎤 Select API", list(apis.keys()))
        api_key_choice = apis[api] 
        language = st.selectbox("🌍 Select Language", list(languages.keys()))
        language_key_choice = languages[language]  

        if st.button("▶ Start Recording"):
            text = transcribe_speech(api_key_choice, language_key_choice)
            st.write("**Transcription:**", text) 
            if text and text not in ["Could not understand audio", "Timeout error"]:
                save_transcription(text)

    elif page == "📂 Upload Audio":
        st.write("Upload an audio file to transcribe using Whisper:")
        uploaded_file = st.file_uploader("Choose an audio file", type=["wav", "mp3", "m4a"])

        if uploaded_file:
            st.audio(uploaded_file, format="audio/mp3")
            text = transcribe_audio_file(uploaded_file)
            st.write("**Transcription:**", text) 
            if text:
                save_transcription(text)

if __name__ == "__main__":
    main()
