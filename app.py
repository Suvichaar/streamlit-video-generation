import streamlit as st
import subprocess
import os
import requests
import re

# Tab setup
tab1, tab2 = st.tabs(["🎬 Subtitle Video Generator", "🎵 Audio Transcription"])

# Tab 1: Subtitle Video Generator
with tab1:
    # First code (Subtitle Video Generator)
   st.header("🎬 Subtitle Video Generator")

    # Sidebar settings for subtitle style
    st.sidebar.header("🎨 Subtitle Styling Settings")
    font_name = st.sidebar.text_area("Font Name", "Nunito")
    font_size = st.sidebar.text_area("Font Size", "62")
    primary_color = st.sidebar.text_area("Primary Colour", "&H00FFFFFF")
    secondary_color = st.sidebar.text_area("Secondary Colour", "&H000000FF")
    outline_color = st.sidebar.text_area("Outline Colour", "&H00000000")
    background_color = st.sidebar.text_area("Background Colour", "&H80000000")
    bold = st.sidebar.text_area("Bold", "-1")
    italic = st.sidebar.text_area("Italic", "0")
    underline = st.sidebar.text_area("Underline", "0")
    strikeout = st.sidebar.text_area("StrikeOut", "0")
    scale_x = st.sidebar.text_area("ScaleX", "100")
    scale_y = st.sidebar.text_area("ScaleY", "100")
    spacing = st.sidebar.text_area("Spacing", "0")
    angle = st.sidebar.text_area("Angle", "0")
    border_style = st.sidebar.text_area("BorderStyle", "1")
    outline = st.sidebar.text_area("Outline", "3")
    shadow = st.sidebar.text_area("Shadow", "2")
    alignment = st.sidebar.text_area("Alignment", "2")
    margin_l = st.sidebar.text_area("MarginL", "10")
    margin_r = st.sidebar.text_area("MarginR", "10")
    margin_v = st.sidebar.text_area("MarginV", "490")
    encoding = st.sidebar.text_area("Encoding", "1")
    
    # Convert HEX and opacity to ASS format
    def hex_to_ass_color(hex_color, opacity=100):
        hex_color = hex_color.lstrip('#')
        alpha = int((100 - opacity) * 2.55)
        return f"&H{alpha:02X}{hex_color[4:6]}{hex_color[2:4]}{hex_color[0:2]}"
    
    # Convert VTT to ASS with custom styling
    def convert_vtt_to_ass(vtt_path, ass_path):
        ass_template = f"""[Script Info]
        Title: Styled Subtitles
        ScriptType: v4.00+
        Collisions: Normal
        PlayDepth: 0
        PlayResX: 1920
        PlayResY: 1080
        
        [V4+ Styles]
        Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
        Style: Default,{font_name},{font_size},{primary_color},{secondary_color},{outline_color},{background_color},{bold},{italic},{underline},{strikeout},{scale_x},{scale_y},{spacing},{angle},{border_style},{outline},{shadow},{alignment},{margin_l},{margin_r},{margin_v},{encoding}
        
        [Events]
        Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        """
            def convert_time(vtt_time):
                h, m, s = vtt_time.split(":")
                s, ms = s.split(".")
                ms = ms[:2]
                return f"{h}:{m}:{s}.{ms}"
        
            with open(vtt_path, "r", encoding="utf-8") as vtt, open(ass_path, "w", encoding="utf-8") as ass:
                ass.write(ass_template)
                lines = vtt.readlines()
                for i in range(len(lines)):
                    if "-->" in lines[i]:
                        start, end = lines[i].strip().split(" --> ")
                        start = convert_time(start)
                        end = convert_time(end)
                        text = lines[i + 1].strip() if i + 1 < len(lines) else ''
                        effect = "{\\fad(500,500)}"
                        if text:
                            ass.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{effect}{text}\n")
            st.success("✅ Subtitle style applied and converted to .ASS format!")
        
        # Upload Files
        vtt_file = st.file_uploader("Upload Subtitle File (.vtt)", type=["vtt"], key="vtt_tab1")
        background_image = st.file_uploader("Upload Background Image", type=["jpg", "jpeg", "png"], key="bg_tab1")
        audio_file = st.file_uploader("Upload Audio File (.mp3)", type=["mp3"], key="audio_tab1")
        
        # Output filename input
        output_filename = st.text_input("Output Video Filename", "final_video.mp4", key="output_tab1")
    
    if st.button("Generate Video 🎥", key="generate_tab1"):
        if vtt_file and background_image and audio_file:
            with open("input_subtitles.vtt", "wb") as f:
                f.write(vtt_file.read())
            with open("background.jpg", "wb") as f:
                f.write(background_image.read())
            with open("audio.mp3", "wb") as f:
                f.write(audio_file.read())
    
            ass_file = "converted_subtitles.ass"
            convert_vtt_to_ass("input_subtitles.vtt", ass_file)
    
            temp_bg_video = "temp_background.mp4"
            temp_final_video = "temp_final.mp4"
    
            try:
                subprocess.run([
                    "ffmpeg", "-y", "-loop", "1", "-i", "background.jpg", "-c:v", "libx264",
                    "-t", "3:14", "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                    "-pix_fmt", "yuv420p", temp_bg_video
                ], check=True)
    
                subprocess.run([
                    "ffmpeg", "-y", "-i", temp_bg_video, "-vf", f"ass={ass_file}", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "18", temp_final_video
                ], check=True)
    
                subprocess.run([
                    "ffmpeg", "-y", "-i", temp_final_video, "-i", "audio.mp3", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", output_filename
                ], check=True)
    
                st.success(f"✅ Successfully created the video: {output_filename}")
                with open(output_filename, "rb") as file:
                    st.download_button("⬇️ Download Video", file, output_filename, key="download_tab1")
    
            except subprocess.CalledProcessError as e:
                st.error(f"Error: {e}")
        else:
            st.error("❌ Please upload all required files.")


# Tab 2: Audio Transcription
with tab2:
    # Second code (Audio Transcription)
    st.header("🎵 Audio Transcription with Azure Whisper")
    st.write("Upload an audio file to transcribe it into subtitles.")

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
            headers = {'api-key': api_key}
            files = {'file': audio_file}
            response = requests.post(
                api_url, headers=headers, files=files,
                data={"response_format": "verbose_json", "temperature": 0.2, "language": "en"}
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

    api_url = st.secrets["azure"]["api_url"]
    api_key = st.secrets["azure"]["api_key"]

    uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"], key="audio_tab2")

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
                        mime="text/vtt",
                        key="download_tab2"
                    )
        os.remove(temp_file_path)
