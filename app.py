import subprocess
import os
import requests
import json
import re

# Azure Whisper API Config
AZURE_API_KEY = st.secrets["azure"]["key"]
AZURE_WHISPER_URL = st.secrets["azure"]["whisper_url"]

# Function to format timestamp for VTT
def format_vtt_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    sec = int(seconds % 60)
    millisec = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{sec:02}.{millisec:03}"

# Simplifying repetitive lyrics
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

# Transcribing audio
def transcribe_audio(file_path):
    if not os.path.exists(file_path):
        print(f"Error: Audio file '{file_path}' not found.")
        return None

    with open(file_path, 'rb') as audio_file:
        headers = {'api-key': AZURE_API_KEY}
        files = {'file': audio_file}
        response = requests.post(
            AZURE_WHISPER_URL, headers=headers, files=files, data={
                "response_format": "verbose_json",
                "temperature": 0.2,
                "language": "en"
            }, timeout=300)
        return response.json() if response.status_code == 200 else None

# Generating VTT subtitle file
def generate_vtt_file(transcript, output_vtt="output.vtt"):
    if not transcript or "segments" not in transcript:
        print("Error: Invalid transcript format or empty response.")
        return

    with open(output_vtt, "w", encoding="utf-8") as vtt_file:
        vtt_file.write("WEBVTT\n\n")
        for segment in transcript["segments"]:
            start_vtt = format_vtt_timestamp(segment["start"])
            end_vtt = format_vtt_timestamp(segment["end"])
            simplified_text = simplify_lyrics(segment["text"])
            vtt_file.write(f"{start_vtt} --> {end_vtt}\n{simplified_text}\n\n")
    print(f".vtt file saved as {output_vtt}")

# Convert VTT to ASS with styling
def convert_vtt_to_ass(vtt_path, ass_path):
    ass_template = """[Script Info]
Title: Styled Subtitles
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Nunito,62,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,10,10,490,1

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

# Burn subtitles and add audio
def burn_subtitles_with_background(vtt_file, background_image, audio_file, output_video):
    ass_file = "converted_subtitles.ass"
    convert_vtt_to_ass(vtt_file, ass_file)

    temp_bg_video = "temp_background.mp4"
    temp_final_video = "temp_final.mp4"

    create_bg_command = [
        "ffmpeg", "-y", "-loop", "1", "-i", background_image, "-c:v", "libx264",
        "-t", "3:14", "-vf",
        "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-pix_fmt", "yuv420p", temp_bg_video
    ]
    subprocess.run(create_bg_command, check=True)

    burn_subs_command = [
        "ffmpeg", "-y", "-i", temp_bg_video, "-vf", f"ass={ass_file}", "-c:v", "libx264",
        "-preset", "slow", "-crf", "18", temp_final_video
    ]
    subprocess.run(burn_subs_command, check=True)

    add_audio_command = [
        "ffmpeg", "-y", "-i", temp_final_video, "-i", audio_file, "-c:v", "copy", "-c:a", "aac",
        "-b:a", "192k", "-shortest", output_video
    ]
    subprocess.run(add_audio_command, check=True)

    os.remove(temp_bg_video)
    os.remove(temp_final_video)
    os.remove(ass_file)

# Main Execution
if __name__ == "__main__":
    # User input
    audio_path = input("Enter the audio file path (e.g., seeyouagain-VEED.mp3): ").strip()
    background_img = input("Enter the background image path (e.g., chrismartin.jpg): ").strip()
    output_video_path = input("Enter the output video name (e.g., Chris-martin-See-you-again-video1.mp4): ").strip()

    # Processing
    transcript = transcribe_audio(audio_path)
    if transcript:
        vtt_file_path = "output_subtitles.vtt"
        generate_vtt_file(transcript, vtt_file_path)
        burn_subtitles_with_background(vtt_file_path, background_img, audio_path, output_video_path)
        print(f"🎉 Video successfully created: {output_video_path}")
    else:
        print("❌ Failed to transcribe the audio.")
