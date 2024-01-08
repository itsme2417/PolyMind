# PolyMind

PolyMind is a multimodal, function calling powered LLM webui. It's designed to be used with Mixtral 8x7B and offers a wide range of features including:

- Internet searching with DuckDuckGo and web scraping capabilities.
- Image generation using comfyui.
- Image input with sharegpt4v (Over llama.cpp's server), OCR, and Yolo.
- Port scanning with nmap.
- A Python interpreter.

The web parts (HTML, JS, CSS, and Flask) are written entirely by Mixtral.

## Installation
1. Clone the repository: `git clone https://github.com/yourusername/polymind.git`
2. Install the required dependencies: `pip install -r requirements.txt`

## Usage

To use PolyMind, run the following command in the project directory:

```bash
python main.py
```

## Configuration

The application's configuration is stored in `config.json` file. Here's a description of each option:

- `Backend`: The backend that runs the LLM. Options: `tabbyapi` or `llama.cpp`.
- `HOST` and `PORT`: The IP address and port of the backend.
- `admin_ip`: The IP address of the admin/trusted user.
- `listen`: Whether to allow other hosts in the network to access the webui.
- `api_key`: The API key for the tabby backend.
- `max_seq_len`: The maximum context length.
- `reserve_space`: Reserves an amount of tokens equivalent to max_new_tokens in the context if set to true.
- `LLM_parameters`: Should be self explanatory, parameters will be overriden by known working ones for now.
- `Enabled_features, image_input, image_generation`: URIs for llama.cpp running a multimodal model and comfyui respectively.

