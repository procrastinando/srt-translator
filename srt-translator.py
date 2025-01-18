import os
import csv
import openai
import streamlit as st
import io
from io import StringIO
import requests
from deep_translator import GoogleTranslator

def address_changed():
    try:
        address = st.session_state["address_input"]
        lang_list = list_lang(address)
        st.session_state["lang_list"] = lang_list
    except:
        pass

def list_lang(address):
    try:
        url = f"http://{address}/languages"
        response = requests.get(url)
        # Check if the request was successful
        if response.status_code == 200:
            languages = response.json()
            return [lang['code'] for lang in languages]
        else:
            st.error(f"Failed to retrieve languages. Status code: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def list_models(address):
    try:
        url = f"http://{address}/api/tags"
        response = requests.get(url)
        response.raise_for_status()
        # Raise an error for bad responses
        models = response.json().get("models", [])
        lista = [model['name'] for model in models]
        return lista if lista else ['No models available!']
    except Exception as e:
        # Catching any exception
        st.error(f"Error: {e}")
        return ['No models available!']

def run_openai(text, model, prompt, contexto, api_key):
    try:
        openai.api_key = api_key  # Set the OpenAI API key
        messages = []
        messages.append({"role": "system", "content": contexto})
        messages.append({"role": "user", "content": f"{prompt}: {text}"})
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages
        )
        # Extract the translated text from the API response
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"OpenAI Error: {e}")
        return text

def run_ollama(text, model, prompt, address):
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "stream": False  # Disable streaming for easier handling of the response
    }
    url = f"http://{address}/api/chat"
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result["message"]["content"].strip()
    except Exception as e:
        st.error(f"Ollama Error: {e}")
        return text

def run_lt(text, address, api_key, source, target):
    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text",
        "api_key": api_key
    }
    headers = {
        "Content-Type": "application/json"
    }
    url = f"https://{address}/translate"
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get('translatedText', text).strip()
        else:
            # Retry with HTTP if HTTPS fails
            url = f"http://{address}/translate"
            response = requests.post(url, json=payload, headers=headers)
            return response.json().get('translatedText', text).strip()
    except Exception as e:
        st.error(f"LibreTranslate Error: {e}")
        return text

def run_google(text, source, target):
    try:
        return GoogleTranslator(source=source, target=target).translate(text=text).strip()
    except Exception as e:
        st.error(f"Google Translate Error: {e}")
        return text

def translate_srt(srt_content, method_choice, model_choice, prompt, context, address, api_key, source, target):
    # Parse the SRT content
    lines = srt_content.strip().split('\n')
    translated_lines = []
    total_lines = len(lines)
    progress_bar = st.progress(0)
    progress_text = st.empty()
    for index, line in enumerate(lines):
        progress = (index + 1) / total_lines
        progress_bar.progress(progress)
        if line.strip().isdigit():
            # Subtitle number
            translated_lines.append(line)
        elif '-->' in line:
            # Timestamp
            translated_lines.append(line)
        elif line.strip() == '':
            # Empty line
            translated_lines.append(line)
        else:
            # Subtitle text
            original_text = line
            if context != 0:
                # Contextual translation can be implemented if needed
                contexto = ""
            else:
                contexto = ""
            if method_choice == 'OpenAI':
                translated_text = run_openai(
                    original_text, model_choice, prompt, contexto, api_key
                )
            elif method_choice == 'Ollama':
                translated_text = run_ollama(
                    original_text, model_choice, prompt, address
                )
            elif method_choice == 'Google':
                translated_text = run_google(
                    original_text, source, target
                )
            else:
                translated_text = run_lt(
                    original_text, address, api_key, source, target
                )
            translated_lines.append(translated_text)
        # Update progress text
        progress_text.text(f"Translated: {index + 1}/{total_lines}")
    # Join the translated lines into a single string
    translated_srt = '\n'.join(translated_lines)
    return translated_srt.encode("utf-8-sig")  # Ensure UTF-8 encoding with BOM

def success(srt_data):
    st.success("Translation complete! Download the file below.")
    st.download_button(
        label="Download Translated SRT",
        data=srt_data,
        file_name="translated_output.srt",
        mime='text/plain'
    )

# Streamlit UI
def main():
    st.title("Subtitle (SRT) Translator App")
    st.sidebar.markdown("""
    ### Subtitle Translation Application

    ## [Original repository](https://github.com/procrastinando/translator)

    This application allows you to translate `.srt` subtitle files into different languages using various translation methods provided by OpenAI, Ollama, Google Translate, and LibreTranslate.

    **Key Features:**
    - Supports multiple translation engines.
    - Maintains subtitle numbering and timing.
    - User-friendly interface with real-time progress updates.
    """)
    
    # Translation method selection
    method_choice = st.selectbox(
        "Choose translation method",
        ("OpenAI", "Ollama", "Google", "LibreTranslate")
    )
    
    # Initialize variables
    prompt = ""
    api_key = ""
    context = 0
    model_choice = ""
    address = ""
    source = ""
    target = ""
    
    if method_choice == "OpenAI":
        prompt = st.text_area(
            "Enter your translation prompt",
            value="Translate the following into English without giving any explanations. If for some reason you can't translate this, simply reply: I can't translate that"
        )
        api_key = st.text_input("Enter your OpenAI API Key", type="password")
        context = st.slider('Select a context size', min_value=0, max_value=20, value=5)
        models_list = ("gpt-4o-mini", "gpt-4o")  # Adjust based on available models
        model_choice = st.selectbox("Choose a model", models_list)
    elif method_choice == "Ollama":
        prompt = st.text_area(
            "Enter your translation prompt",
            value="Translate the following into English without giving any explanations. If for some reason you can't translate this, simply reply: I can't translate that"
        )
        address = st.text_input("Enter Ollama address", value="localhost:11434")
        models_list = list_models(address)
        model_choice = st.selectbox("Choose a model", models_list)
    elif method_choice == "Google":
        google_list = [
            'af', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn', 'bs', 'bg', 'ca',
            'ceb', 'ny', 'zh-cn', 'zh-tw', 'co', 'hr', 'cs', 'da', 'nl', 'en',
            'eo', 'et', 'tl', 'fi', 'fr', 'fy', 'gl', 'ka', 'de', 'el', 'gu',
            'ht', 'ha', 'haw', 'iw', 'hi', 'hmn', 'hu', 'is', 'ig', 'id', 'ga',
            'it', 'ja', 'jw', 'kn', 'kk', 'km', 'rw', 'ko', 'ku', 'ky', 'lo',
            'la', 'lv', 'lt', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'mi', 'mr',
            'mn', 'my', 'ne', 'no', 'or', 'ps', 'fa', 'pl', 'pt', 'pa', 'ro',
            'ru', 'sm', 'gd', 'sr', 'st', 'sn', 'sd', 'si', 'sk', 'sl', 'so',
            'es', 'su', 'sw', 'sv', 'tg', 'ta', 'tt', 'te', 'th', 'tr', 'tk',
            'uk', 'ur', 'ug', 'uz', 'vi', 'cy', 'xh', 'yi', 'yo', 'zu'
        ]
        source = st.selectbox("From:", ['auto'] + google_list)
        target = st.selectbox("To:", google_list)
    else:  # LibreTranslate
        if "lang_list" not in st.session_state:
            st.session_state["lang_list"] = []
        address = st.text_input(
            "Enter LibreTranslate address",
            value="localhost:5000",
            key="address_input",
            on_change=address_changed
        )
        api_key = st.text_input("Enter your LibreTranslate API Key", type="password")
        if st.session_state["lang_list"]:
            source = st.selectbox("From:", ['auto'] + st.session_state["lang_list"])
            target = st.selectbox("To:", st.session_state["lang_list"])
        else:
            st.selectbox("From:", ['auto'])
            st.selectbox("To:", [])
    
    # File uploader for SRT files
    input_file = st.file_uploader("Upload an SRT file", type="srt")
    
    if input_file:
        # Run button
        if st.button("Run"):
            try:
                # Read the SRT file content
                srt_content = input_file.getvalue().decode("utf-8")
            except UnicodeDecodeError:
                st.error("Error decoding the file. Please ensure it's in UTF-8 or Windows-1252 encoding.")
                try:
                    srt_content = input_file.getvalue().decode("windows-1252")
                except Exception as e:
                    st.error(f"Failed to decode the file: {e}")
                    srt_content = ""
            
            if srt_content:
                # Translate the SRT content
                if method_choice == "OpenAI":
                    translated_srt = translate_srt(
                        srt_content,
                        method_choice=method_choice,
                        model_choice=model_choice,
                        prompt=prompt,
                        context=context,
                        address='',
                        api_key=api_key,
                        source='',
                        target=''
                    )
                    success(translated_srt)
                elif method_choice == "Ollama":
                    translated_srt = translate_srt(
                        srt_content,
                        method_choice=method_choice,
                        model_choice=model_choice,
                        prompt=prompt,
                        context=0,
                        address=address,
                        api_key='',
                        source='',
                        target=''
                    )
                    success(translated_srt)
                elif method_choice == "Google":
                    translated_srt = translate_srt(
                        srt_content,
                        method_choice=method_choice,
                        model_choice='',
                        prompt='',
                        context=0,
                        address='',
                        api_key='',
                        source=source,
                        target=target
                    )
                    success(translated_srt)
                else:  # LibreTranslate
                    translated_srt = translate_srt(
                        srt_content,
                        method_choice=method_choice,
                        model_choice='',
                        prompt='',
                        context=0,
                        address=address,
                        api_key=api_key,
                        source=source,
                        target=target
                    )
                    success(translated_srt)
            else:
                st.error("Failed to read the file content.")
    else:
        st.info("Please upload an SRT file to begin translation.")

if __name__ == "__main__":
    main()