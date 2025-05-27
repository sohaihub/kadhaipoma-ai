import streamlit as st
import requests
import base64
import io
import wave
import google.generativeai as genai


# Gemini API key (your provided key)
GEMINI_API_KEY = "AIzaSyDDHNQB3EyoVsmAZi6Gh-aaEyVFl-F7-bI"

# Sarvam TTS API details
API_KEY_SARVAM = "sk_v4ka9u7i_b869GOmkZ5PdM5M6JR1GyZHw"
API_URL_SARVAM = "https://api.sarvam.ai/text-to-speech"
MAX_CHARS = 100  # Adjust as per API limit

# Initialize Gemini client
genai.configure(api_key=GEMINI_API_KEY)  # ✅ correct


def chunk_text(text, size):
    """Split text into chunks without breaking words."""
    words = text.strip().split()
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk) + len(word) + 1 <= size:
            current_chunk += (" " if current_chunk else "") + word
        else:
            chunks.append(current_chunk)
            current_chunk = word
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def call_sarvam_tts(text_chunk, lang_code, speaker):
    headers = {
        "api-subscription-key": API_KEY_SARVAM,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text_chunk.strip(),
        "target_language_code": lang_code,
        "speaker": speaker,
        "model": "bulbul:v1"
    }
    response = requests.post(API_URL_SARVAM, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['audios'][0]

def merge_wav_base64(audio_base64_list):
    wav_buffers = []
    params = None
    for b64 in audio_base64_list:
        wav_bytes = base64.b64decode(b64)
        buffer = io.BytesIO(wav_bytes)
        with wave.open(buffer, 'rb') as w:
            if params is None:
                params = w.getparams()
            frames = w.readframes(w.getnframes())
            wav_buffers.append(frames)

    merged_frames = b"".join(wav_buffers)
    output_buffer = io.BytesIO()
    with wave.open(output_buffer, 'wb') as w_out:
        w_out.setparams(params)
        w_out.writeframes(merged_frames)

    return output_buffer.getvalue()

def generate_story(title, language):
    prompt = (
        f"Generate a {language} story titled '{title}', "
        "with sentences separated by commas, duration about 2 to 3 minutes, "
        "and end with a moral."
        "include only the story and moral at the end, no translation or explanation."
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )
    return response.text.strip()

def main():
    st.title("Kadhaipoma.ai - Streamlit Version")

    title = st.text_input("Enter Story Title:")
    language = st.selectbox("Select Language", ["English", "Tamil"])

    lang_map = {
        "English": ("en-IN", "meera"),
        "Tamil": ("ta-IN", "pavithra")
    }

    if st.button("Generate Story and Audio"):
        if not title.strip():
            st.error("Please enter a story title.")
            return

        if language not in lang_map:
            st.error("Unsupported language selected.")
            return

        try:
            with st.spinner("Generating story..."):
                story_text = generate_story(title, language)

            st.markdown("### Generated Story:")
            st.write(story_text)

            chunks = chunk_text(story_text, MAX_CHARS)
            st.info(f"Text split into {len(chunks)} chunk(s) for audio processing.")

            audio_chunks = []
            lang_code, speaker = lang_map[language]

            for i, chunk in enumerate(chunks, 1):
                st.write(f"Processing audio chunk {i} of {len(chunks)}...")
                audio_b64 = call_sarvam_tts(chunk, lang_code, speaker)
                audio_chunks.append(audio_b64)

            merged_audio = merge_wav_base64(audio_chunks)
            st.success("✅ Audio generated and merged successfully!")

            st.audio(merged_audio, format="audio/wav")
            st.download_button("📥 Download Audio", merged_audio, file_name="story_audio.wav", mime="audio/wav")

        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
