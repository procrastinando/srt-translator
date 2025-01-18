# Subtitle Translator

### Subtitle (SRT) Translation Application Overview

This code implements a **Subtitle (SRT) Translation Application** using **Streamlit**, which allows users to translate the contents of an SRT file into different languages through various translation methods. Here's a breakdown of its key components:

#### Libraries Used
- **`os`, `requests`, `io`, `time`**: For handling file operations, HTTP requests, and data manipulation.
- **`openai`**: To interact with OpenAI's translation models.
- **`streamlit`**: For building the web interface.
- **`deep_translator`**: To interact with Google Translate API.

#### Main Functions
- **`address_changed()`**: Updates the list of available languages when the address input changes.
- **`list_lang(address)`**: Fetches available languages from a specified address using an HTTP GET request.
- **`list_models(address)`**: Retrieves available models from a server endpoint, handling errors gracefully.
- **`run_openai(text, model, prompt, api_key)`**: Calls the OpenAI API to translate the provided text using the specified model.
- **`run_ollama(text, model, prompt, address)`**: Uses the Ollama API to perform translations.
- **`run_lt(text, address, api_key, source, target)`**: Sends translation requests to LibreTranslate, managing the input and output format.
- **`run_google(text, source, target)`**: Utilizes Google Translate to translate the provided text.
- **`translate_srt(srt_content, method_choice, model_choice, prompt, context, address, api_key, source, target)`**: Reads SRT content, applies the selected translation method to each subtitle text, and updates a progress bar in the Streamlit interface.
- **`success(srt_data)`**: Displays a success message and offers a download button for the translated SRT file.

#### User Interface
The application sets up a web page where users can select the translation method (OpenAI, Ollama, Google Translate, or LibreTranslate), input their translation prompt, API keys, and upload an SRT file for translation. It processes the uploaded file based on the user's chosen method and provides feedback through progress indicators and success messages.

### 1. Install Requirements
To set up the environment and install necessary dependencies, follow these steps:

```bash
# Create a new conda environment named 'subtitle_translator' with Python 3.10
conda create --name subtitle_translator python=3.10 -y

# Activate the environment
conda activate subtitle_translator

# Clone the repository containing the Subtitle Translator
git clone https://github.com/procrastinando/srt-translator

# Navigate into the project directory
cd subtitle-translator

# Install the required Python packages
pip install -r requirements.txt
