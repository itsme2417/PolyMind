# PolyMind

PolyMind is a multimodal, function calling powered LLM webui. It's designed to be used with Mixtral 8x7B + TabbyAPI and offers a wide range of features including:

- Internet searching with DuckDuckGo and web scraping capabilities.
- Image generation using comfyui.
- Image input with sharegpt4v (Over llama.cpp's server), OCR, and Yolo.
- Port scanning with nmap.
- Wolfram Alpha integration.
- A Python interpreter.

The web parts (HTML, JS, CSS, and Flask) are written entirely by Mixtral.

Note: The python interpreter is intentionally delayed by 5 seconds to make it easy to check the code before its ran.

## Installation
1. Clone the repository: `git clone https://github.com/yourusername/polymind.git`
2. Install the required dependencies: `pip install -r requirements.txt`
3. Copy `config.example.json` as `config.json` and fill in required settings.

## Usage

To use PolyMind, run the following command in the project directory:

```bash
python main.py
```
There are no "commands" or similar as everything is done via function calling. Clearing the context can be done by asking the model to do so, along with the Enabled features which can be disabled or enabled temporarily in the same way.

## Configuration

The application's configuration is stored in the `config.json` file. Here's a description of each option:

- `Backend`: The backend that runs the LLM. Options: `tabbyapi` or `llama.cpp`. (Currently only TabbyAPI is fully supported.)
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

## Donations

Patreon: https://www.patreon.com/llama990

LTC: Le23XWF6bh4ZAzMRK8C9bXcEzjn5xdfVgP

XMR: 46nkUDLzVDrBWUWQE2ujkQVCbWUPGR9rbSc6wYvLbpYbVvWMxSjWymhS8maYdZYk8mh25sJ2c7S93VshGAij3YJhPztvbTb

If you want to mess around with my llm discord bot or join for whatever reason, heres a discord server:
https://discord.gg/zxPCKn859r

## Screenshots
![screenshot0](/images/screenshot0.png)
![screenshot1](/images/screenshot1.png)
![screenshot2](/images/screenshot2.png)
![screenshot3](/images/screenshot3.png)
