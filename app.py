import streamlit as st
import requests
import re
import os

def format_vtt_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    sec = int(seconds % 60)
    millisec = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{sec:02}.{millisec:03}"

def simplify_lyrics(text):
    pattern_oh = r'(Oh(\s+Oh)*)'
    pattern_la = r'(La(\s+La)*)'
    pattern_na = r'(Na(\s+Na)*)'
    
    if re.match(pattern_oh, text, re.IGNORECASE):
        return "Chorus: Oh (singing)"
    elif re.match(pattern_la, text, re.IGNORECASE):
        return "Chorus: La (singing)"
    elif re.match(pattern_na, text, re.IGNORECASE):
        return "Chorus: Na (singing)"
    
    text = re.sub(r'\s+', ' ', text.strip())
    if len(text) > 40:
        text = text[:37] + "..."
    return text

def transcribe_audio(file_path, api_key, api_url):
    with open(file_path, 'rb') as audio_file:
        headers = {
            'api-key': api_key,
        }
        files = {'file': audio_file}
        response = requests.post(
            api_url,
            headers=headers,
            files=files,
            data={
                "response_format": "verbose_json",
                "temperature": 0.2,
                "language": "en"
            }
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code}, {response.text}")
            return None

def generate_vtt_file(transcript, output_vtt="transcription.vtt", max_duration_per_subtitle=10.0):
    if not transcript or "segments" not in transcript:
        st.error("Invalid transcript format or empty response.")
        return None

    segments = transcript["segments"]
    with open(output_vtt, "w", encoding="utf-8") as vtt_file:
        vtt_file.write("WEBVTT\n\n")
        for segment in segments:
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()

            if not text or len(text) < 1:
                continue

            simplified_text = simplify_lyrics(text)

            if (end - start) > max_duration_per_subtitle:
                chunk_duration = max_duration_per_subtitle
                current_start = start
                while current_start < end:
                    chunk_end = min(current_start + chunk_duration, end)
                    start_vtt = format_vtt_timestamp(current_start)
                    end_vtt = format_vtt_timestamp(chunk_end)
                    chunk_text = simplified_text if (chunk_end - current_start) <= max_duration_per_subtitle else f"{simplified_text} (cont.)"
                    vtt_file.write(f"{start_vtt} --> {end_vtt}\n{chunk_text}\n\n")
                    current_start += chunk_duration
            else:
                start_vtt = format_vtt_timestamp(start)
                end_vtt = format_vtt_timestamp(end)
                vtt_file.write(f"{start_vtt} --> {end_vtt}\n{simplified_text}\n\n")
    return output_vtt

# Streamlit App
st.title("🎵 Audio Transcription with Azure Whisper")
st.write("Upload an audio file to transcribe it into subtitles.")

api_key = st.text_input("Enter your Azure API Key:", type="password")
api_url = st.text_input("Enter your Azure Whisper API URL:")
uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"])

if uploaded_file and api_key and api_url:
    temp_file_path = os.path.join("temp_audio", uploaded_file.name)
    os.makedirs("temp_audio", exist_ok=True)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.read())

    st.info("Transcribing audio, please wait...")
    transcript = transcribe_audio(temp_file_path, api_key, api_url)

    if transcript:
        st.success("Transcription successful!")
        vtt_file = generate_vtt_file(transcript)
        if vtt_file:
            with open(vtt_file, "rb") as file:
                st.download_button(
                    label="Download VTT File",
                    data=file,
                    file_name="transcription.vtt",
                    mime="text/vtt"
                )
    os.remove(temp_file_path)
