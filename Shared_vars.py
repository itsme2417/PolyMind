from pathlib import Path
import os
import json

mem = {}
vismem = {}
blipcache = {}


class Config:
    def __init__(self):
        script_dir = Path(os.path.abspath(__file__)).parent

        with open(os.path.join(script_dir, "config.json")) as config_file:
            config = json.load(config_file)
        self.listen = config["listen"]
        self.llm_parameters = config["LLM_parameters"]
        self.backend = config["Backend"]
        self.host = config["HOST"].rstrip("/") if config["HOST"].endswith("/") else config["HOST"]
        self.port = config["PORT"]
        self.enabled_features = config["Enabled_features"]
        self.adminip = config["admin_ip"]
        self.api_key = config["api_key"]
        self.ctxlen = config["max_seq_len"]
        self.reservespace = config["reserve_space"]
        print("Loaded config")


config = Config()
API_ENDPOINT_URI = f"{config.host}:{config.port}/" if config.host.lower().startswith('http') else  f"http://{config.host}:{config.port}/"

API_KEY = config.api_key

TABBY = True if config.backend == "tabbyapi" else False
address = "0.0.0.0" if config.listen else "127.0.0.1"
loadedfile = {}


if (
    config.enabled_features["wolframalpha"]["enabled"]
    and config.enabled_features["wolframalpha"]["app_id"] == ""
    or config.enabled_features["wolframalpha"]["app_id"] == "your-wolframalpha-app-id"
):
    config.enabled_features["wolframalpha"]["enabled"] = False
    print(
        "\033[93m WARN: Wolfram Alpha has been disabled because no app_id was provided. \033[0m"
    )

if config.api_key == "your-tabby-api-key" or config.api_key == "":
    print(
        "\033[93m WARN: You have not set an API key, You probably want to set this if using TabbyAPI. \033[0m"
    )
