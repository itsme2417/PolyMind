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

        self.backend = config["Backend"]
        self.host = config["HOST"]
        self.port = config["PORT"]
        self.base_context = config["Base_Context"]
        self.model_name = config["model_Name"]
        self.enabled_features = config["Enabled_features"]
        self.llm_parameters = config["LLM_parameters"]
        self.adminip = config["admin_ip"]
        self.api_key = config["api_key"]
        self.ctxlen = config["max_seq_len"]
        self.reservespace = config["reserve_space"]
        print("Loaded config")


config = Config()
API_ENDPOINT_URI = f"http://{config.host}:{config.port}/"
API_KEY = config.api_key

TABBY = True if config.backend == "tabbyapi" else False
address = "0.0.0.0" if config.listen else "127.0.0.1"
