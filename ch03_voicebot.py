##### 기본 정보 입력 #####
import streamlit as st
from audiorecorder import audiorecorder
from openai import OpenAI
import os
from datetime import datetime
import numpy as np
from gtts import gTTS
import base64

##### OpenAI 객체 생성 함수 #####
def get_openai_client(api_key):
    return OpenAI(api_key=api_key)

##### 기능 구현 함수 #####
def STT(audio, client):
    # 파일 저장
    filename = 'input.mp3'
    with open(filename, "wb") as wav_file:
        wav_file.write(audio.tobytes())

    with open(filename, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    os.remove(filename)
    return transcript.text

def ask_gpt(prompt, model, client):
    response = client.chat.completions.create(
        model=model,
        messages=prompt
    )
    return response.choices[0].message.content

def TTS(response):
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)

    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
        """
        st.markdown(md, unsafe_allow_html=True)
    os.remove(filename)

##### 메인 함수 #####
def main():
    st.set_page_config(page_title="음성 비서 프로그램", layout="wide")
    flag_start = False

    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]

    if "check_audio" not in st.session_state:
        st.session_state["check_audio"] = []

    st.header("음성 비서 프로그램")
    st.markdown("---")

    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write("""
        - 음성비서 프로그램의 UI는 스트림릿을 활용했습니다.
        - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용했습니다. 
        - 답변은 OpenAI의 GPT 모델을 활용했습니다. 
        - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용했습니다.
        """)

    with st.sidebar:
        api_key = st.text_input("OPENAI API 키", placeholder="Enter Your API Key", value="", type="password")
        model = st.radio("GPT 모델", options=["gpt-4", "gpt-3.5-turbo"])

        if st.button("초기화"):
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]

    if not api_key:
        st.warning("OpenAI API 키를 입력하세요.")
        return

    client = get_openai_client(api_key)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("질문하기")
        audio = audiorecorder("클릭하여 녹음하기", "녹음중...")
        if len(audio) > 0 and not np.array_equal(audio, st.session_state["check_audio"]):
            st.audio(audio.tobytes())
            question = STT(audio, client)

            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"].append(("user", now, question))
            st.session_state["messages"].append({"role": "user", "content": question})
            st.session_state["check_audio"] = audio
            flag_start = True

    with col2:
        st.subheader("질문/답변")
        if flag_start:
            response = ask_gpt(st.session_state["messages"], model, client)
            st.session_state["messages"].append({"role": "system", "content": response})
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"].append(("bot", now, response))

            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")

            TTS(response)

if __name__ == "__main__":
    main()
