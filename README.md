# PolyMind

PolyMind is a multimodal, function calling powered LLM webui. It's designed to be used with Mixtral 8x7B-Instruct/Mistral-7B-Instruct-v0.2 + TabbyAPI, but can be used with other models and/or with llama.cpp's included server and, when using the compatiblity mode + tabbyAPI mode, any endpoint with /v1/completions support, and offers a wide range of features including:

- Internet searching with DuckDuckGo and web scraping capabilities.
- Image generation using comfyui along with optional, function calling controlled, automatic background removal using RMBG-1.4 and experimental img2img with uploaded images.
- Image input with sharegpt4v (Over llama.cpp's server)/moondream on CPU, OCR, and Yolo.
- Port scanning with nmap.
- Wolfram Alpha integration.
- A Python interpreter.
- RAG with semantic search for PDF and miscellaneous text files.
- Plugin system to easily add extra functions that are able to be called by the model.

90% of the web parts (HTML, JS, CSS, and Flask) are written entirely by Mixtral.

Note: The python interpreter is intentionally delayed by 5 seconds to make it easy to check the code before its ran.

Note: When making multiple function calls simultaneously, only one image can be returned at a time. For instance, if you request to generate an image of a dog using comfyui and plot a sine wave using matplotlib, only one of them will be displayed.

Note: When using RAG, make it clear that you are requesting information according to the file you've uploaded.

## Installation
1. Clone the repository: `git clone https://github.com/itsme2417/PolyMind.git && cd PolyMind`
2. Install the required dependencies: `pip install -r requirements.txt`
3. Install the required node modules: `cd static && npm install`
4. Copy `config.example.json` as `config.json` and fill in required settings.

For the ComfyUI stablefast workflow, make sure to have [ComfyUI_stable_fast](https://github.com/gameltb/ComfyUI_stable_fast) installed.
For the img2img workflow, make sure to have [comfyui-base64-to-image](https://github.com/glowcone/comfyui-base64-to-image) installed.

## Usage

To use PolyMind, run the following command in the project directory:

```bash
python main.py
```
There are no "commands" or similar as everything is done via function calling. Clearing the context can be done by asking the model to do so, along with the Enabled features which can be disabled or enabled temporarily in the same way.

For plugins check [The plugins directory](https://github.com/itsme2417/PolyMind/tree/main/plugins)

For an example on how to use polymind as a basic API Server check [Examples](https://github.com/itsme2417/PolyMind/tree/main/examples/discord_bot)

## Configuration

The application's configuration is stored in the `config.json` file. Here's a description of each option:

- `Backend`: The backend that runs the LLM. Options: `tabbyapi` or `llama.cpp`.
- `compatibility_mode`, `compat_tokenizer_model`: When set to true and a tokenizer model specified, will use a local tokenizer instead of one provided by the API server. To be used with endpoints without tokenization support, such as `KoboldCPP` or similar.
- `HOST` and `PORT`: The IP address and port of the backend.
- `admin_ip`: The IP address of the admin/trusted user. Necessary to use the Python interpreter and change settings.
- `listen`: Whether to allow other hosts in the network to access the webui.
- `api_key`: The API key for the Tabby backend.
- `max_seq_len`: The maximum context length.
- `reserve_space`: Reserves an amount of tokens equivalent to `max_new_tokens` in the context if set to true.
- `LLM_parameters`: Should be self-explanatory, parameters will be overridden by known working ones for now.
- `Enabled_features`, `image_input`, `imagegeneration`, `wolframalpha`: URIs for llama.cpp running a multimodal model, comfyui, and the app_id for Wolfram Alpha respectively.
- `runpythoncode/depth`: Specifies the maximum number of attempts GateKeeper can make to debug non-running code. To disable this feature, set it to 0.
- `imagegeneration/checkpoint_name`: Specifies the filename of the SD checkpoint for comfyui.
- `file_input/chunk_size`: Specifies the token count per segment for text chunking. Equivalent to amount of context used per RAG message.
- `file_input/raw_input`: If set to true, the user's message is used as the query for the semantic search, otherwise an LLM generated query is used.
- `file_input/retrieval_count`: Number of chunks to use from the RAG results.
- `image_input/backend`: If set to `moondream`, will use the moondream model on cpu, if set to `llama.cpp` will use the llama.cpp server running at `URI`.
- `Plugins`: A list containing the name of enabled plugins, Names should match the folder names in `plugins` and `module_name` from their `manifest.json`. 

## Donations

Patreon: https://www.patreon.com/llama990

LTC: Le23XWF6bh4ZAzMRK8C9bXcEzjn5xdfVgP

XMR: 46nkUDLzVDrBWUWQE2ujkQVCbWUPGR9rbSc6wYvLbpYbVvWMxSjWymhS8maYdZYk8mh25sJ2c7S93VshGAij3YJhPztvbTb

If you want to mess around with my llm discord bot or join for whatever reason, heres a discord server:
https://discord.gg/zxPCKn859r

## Screenshots
[![screenshot0](/images/thumb.screenshot0.png)](/images/screenshot0.png)
[![screenshot1](/images/thumb.screenshot1.png)](/images/screenshot1.png)
[![screenshot2](/images/thumb.screenshot2.png)](/images/screenshot2.png)
[![screenshot3](/images/thumb.screenshot3.png)](/images/screenshot3.png)
[![screenshot4](/images/thumb.screenshot4.png)](/images/screenshot4.png)
[![screenshot5](/images/thumb.screenshot5.png)](/images/screenshot5.png)