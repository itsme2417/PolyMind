## Plugins
Polymind supports adding extra functions that the model can access. Included is an example plugin that allows the model to ask chatgpt questions.

## Adding / Developing plugins

The format of plugins is a folder under the plugins directory, a `main.py` file and `manifest.json`. the name of the plugin should match the "module_name" under manifest.json and is the name that will be used to enable the plugin in the config.json.


The `manifest.json` file contains metadata about the plugin, such as the module name, name, description, and parameters. Here is an example `manifest.json` file:

```
{
    "module_name": "chatgpt",
    "name": "askchatgpt",
    "description": "This sends a message to chatgpt.",
    "params": {
        "message": "The message to send to the ChatGPT API. Should be 1:1 with the message requested by the user, for example: 'ask chatgpt if cats or dogs are better' would give a message of: 'are cats or dogs better?'"
    }
}
```


* `module_name`: The name of the plugin.
* `name`: The internal name of the plugin which the model will be seeing / calling.
* `description`: A description of what the function does, also meant for the model.
* `params`: The parameters that the model can include with its function call. Should include a description of what to be expected so the model can use it properly.

The `main.py` file should contain the following format:

```def main(params, memory, infer, ip):

    return f"This will be sent to the model"
if __name__ == "__main__":
    main(params, memory, infer, ip)```

    
params is a dict contained any parameters from the function call, memory is polymind's context and infer is a function to do inference using the main model. [See inference.py](https://github.com/itsme2417/PolyMind/blob/main/inference.py) ip is the ip of the user who sent the request.