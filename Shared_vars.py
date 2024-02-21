from pathlib import Path
import sys
import os
import json
import importlib.util

mem = {}
vismem = {}
blipcache = {}

script_dir = Path(os.path.abspath(__file__)).parent

class Config:
    def __init__(self):

        with open(os.path.join(script_dir, "config.json")) as config_file:
            config = json.load(config_file)
        self.listen = config["listen"]
        self.llm_parameters = config["LLM_parameters"]
        self.backend = config["Backend"]
        self.host = (
            config["HOST"].rstrip("/")
            if config["HOST"].endswith("/")
            else config["HOST"]
        )
        try:
            self.plugins = config["Plugins"]
        except KeyError:
            print("Plugins disabled.")
            self.plugins = []
        self.port = config["PORT"]
        self.system = config['system_prompt']
        self.enabled_features = config["Enabled_features"]
        self.adminip = config["admin_ip"]
        self.api_key = config["api_key"]
        self.ctxlen = config["max_seq_len"]
        self.reservespace = config["reserve_space"]
        try:
            self.compat = config["compatibility_mode"]
            self.tokenmodel = config["compat_tokenizer_model"]
        except KeyError:
            print(
                "\033[93m WARN: Config is missing compatibility_mode, Update your config to comply with the latest example config. \033[0m"
            )   
        print("Loaded config")


config = Config()
API_ENDPOINT_URI = (
    f"{config.host}:{config.port}/"
    if config.host.lower().startswith("http")
    else f"http://{config.host}:{config.port}/"
)

API_KEY = config.api_key

TABBY = True if config.backend == "tabbyapi" else False
address = "0.0.0.0" if config.listen else "127.0.0.1"
loadedfile = {}

if not "retrieval_count" in config.enabled_features["file_input"] and config.enabled_features["file_input"]["enabled"]:
    print(
        "\033[91mERROR: retrieval_count missing from file_input config, Update your config, Exiting... \033[0m"
    )        
    sys.exit()
if config.compat:
    if config.tokenmodel == "":
        print(
            "\033[91mERROR: Compatibility_mode is set to true but no tokenizer model is set, Exiting... \033[0m"
        )        
    sys.exit()
if (
    config.enabled_features["wolframalpha"]["enabled"]
    and (config.enabled_features["wolframalpha"]["app_id"] == ""
    or config.enabled_features["wolframalpha"]["app_id"] == "your-wolframalpha-app-id")
):
    config.enabled_features["wolframalpha"]["enabled"] = False
    print(
        "\033[93m WARN: Wolfram Alpha has been disabled because no app_id was provided. \033[0m"
    )

if config.api_key == "your-tabby-api-key" or config.api_key == "":
    print(
        "\033[93m WARN: You have not set an API key, You probably want to set this if using TabbyAPI. \033[0m"
    )


def import_plugin(plugin_directory, plugin_name):
    main_path = os.path.join(plugin_directory, plugin_name, 'main.py')
    spec = importlib.util.spec_from_file_location(f"{plugin_name}.main", main_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_plugins():
    config_plugins = config.plugins
    plugdict = {}
    if len(config_plugins) < 1:
        return [], {}
    manifests = []

    for folder_name in os.listdir(os.path.join(script_dir, 'plugins')):
        if folder_name in config_plugins:
            print(f"loading plugin: {folder_name}")
            manifest_path = os.path.join(script_dir, 'plugins', folder_name, 'manifest.json')
            try:
                with open(manifest_path, 'r') as file:
                    loadedjson = json.load(file)
                    manifests.append(loadedjson)
                    plugdict[loadedjson['module_name']] = import_plugin(os.path.join(script_dir, "plugins"), loadedjson['module_name'])
            except FileNotFoundError:
                print(f"Manifest file not found for plugin: {folder_name}")
            except json.JSONDecodeError:
                print(f"Error decoding JSON from manifest of plugin: {folder_name}")

    return manifests, plugdict

plugin_manifests, loadedplugins = load_plugins()