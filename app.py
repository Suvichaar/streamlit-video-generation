import streamlit as st
import requests
import os
import re
from pathlib import Path

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
    return text[:37] + "..." if len(text) > 40 else text

def transcribe_audio(file_path, api_url, api_key):
    with open(file_path, 'rb') as audio_file:
        headers = {'api-key': api_key}
        files = {'file': audio_file}
        response = requests.post(api_url, headers=headers, files=files, timeout=300)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code}, {response.text}")
            return None

def generate_vtt_file(transcript, max_duration_per_subtitle=10.0):
    vtt_content = "WEBVTT\n\n"
    segments = transcript.get("segments", [])
    for segment in segments:
        start = segment["start"]
        end = segment["end"]
        text = simplify_lyrics(segment["text"].strip())
        if not text:
            continue
        if (end - start) > max_duration_per_subtitle:
            chunk_duration = max_duration_per_subtitle
            current_start = start
            while current_start < end:
                chunk_end = min(current_start + chunk_duration, end)
                start_vtt = format_vtt_timestamp(current_start)
                end_vtt = format_vtt_timestamp(chunk_end)
                vtt_content += f"{start_vtt} --> {end_vtt}\n{text}\n\n"
                current_start += chunk_duration
        else:
            start_vtt = format_vtt_timestamp(start)
            end_vtt = format_vtt_timestamp(end)
            vtt_content += f"{start_vtt} --> {end_vtt}\n{text}\n\n"
    return vtt_content

def main():
    st.title("🎵 Song Transcriber with Azure Whisper API")
    st.write("Upload an audio file to generate subtitles.")

    # Load secrets
    api_url = st.secrets["azure"]["api_url"]
    api_key = st.secrets["azure"]["api_key"]

    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])

    if uploaded_file and api_url and api_key:
        file_path = os.path.join("temp", uploaded_file.name)
        os.makedirs("temp", exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.info("Transcribing audio...")
        transcript = transcribe_audio(file_path, api_url, api_key)
        
        if transcript:
            st.success("Transcription completed!")
            vtt_content = generate_vtt_file(transcript)
            vtt_file_path = f"{Path(uploaded_file.name).stem}.vtt"
            with open(vtt_file_path, "w", encoding="utf-8") as vtt_file:
                vtt_file.write(vtt_content)
            
            st.download_button(
                label="Download VTT File",
                data=vtt_content,
                file_name=vtt_file_path,
                mime="text/vtt"
            )

if __name__ == "__main__":
    main()
