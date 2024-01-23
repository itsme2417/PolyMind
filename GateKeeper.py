from openai import OpenAI
import os
import json
import re
import html
import time
import wolframalpha
from duckduckgo_search import DDGS
import nmap
import traceback

from datetime import datetime
import subprocess
import Shared_vars
from comfyui import imagegen
from inference import infer
from scrape import scrape_site
if Shared_vars.config.enabled_features["file_input"]["enabled"]:
    from FileHandler import queryEmbeddings
import requests
from PIL import Image
from io import BytesIO
from pathlib import Path

path = Path(os.path.abspath(__file__)).parent
client = OpenAI(
    base_url=f"http://{Shared_vars.config.host}:{Shared_vars.config.port}/v1",
    api_key=Shared_vars.config.api_key,
)
func = ""
client = wolframalpha.Client(
    Shared_vars.config.enabled_features["wolframalpha"]["app_id"]
)

with open(os.path.join(path,"functions.json")) as user_file:
    global searchfunc
    fcontent = json.loads(user_file.read())
    for x in fcontent:
        params = (
            json.dumps(x["params"])
            .strip("{}")
            .replace('",', "\n           ")
            .replace('"', "")
        )
        template = f"""\n{x['name']}:
        description: {x['description']}
        params:
            {params}"""

        if x['name'] == "searchfile":
            searchfunc = template
            continue
        else:
            func += template


def get_image_size(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img.size[0] + img.size[1]


def GateKeep(input, ip, depth=0, stream=False):
    content = ""
    print("Begin streamed GateKeeper output.")
    examplefnc = '<startfunc>{\n"function": "internetsearch",\n"params": {\n"keywords": "mixtral"\n}\n}<endfunc>'
    funclist = func
    try:
        if Shared_vars.loadedfile[ip] != {}:
            funclist += searchfunc
    except Exception:
        pass
    try:
        ctxstr = ""
        for x in Shared_vars.vismem[f"{ip}"][-2:]:
            ctxstr += re.sub(
                r"!\[.*?\]\(.*?\)|<img.*?>|\[\{.*?\}\]",
                "",
                "USER: " + x["user"] + "\n" + "PolyMind: " + x["assistant"],
            )
        content = 'Output:\n<startfunc>\n[{\n  "function": "'
        content += next(infer(
            "Input: " + input,
            mem=[],
            modelname='Output:\n<startfunc>\n[{\n  "function": "',
            system=f"You are an AI assistant named GateKeeper, The current date is {datetime.now()}, please select the single most suitable function and parameters from the list of available functions below, based on the user's input and pay attention to the context, which will then be passed over to polymind. Provide your response in JSON format surrounded by '<startfunc>' and '<endfunc>' without any notes, comments or follow-ups. Only JSON.\n{funclist}\nContext: {ctxstr}\n",
            temperature=0.1,
            top_p=0.1,
            min_p=0.05,
            top_k=40,
            stopstrings=[
                "Input: ",
                "[INST]",
                "[/INST]",
                "```",
                "</s>",
                "user:",
                "polymind:",
                "Polymind:",
                "<</SYS>>",
                "[System Message]",
                "endfunc",
                "<endfunc>",
                "}<",
                "</startfunc>",
            ],
            max_tokens=500,
        ))[0]
    except TypeError:
        content = 'Output:\n<startfunc>\n[{\n  "function": "'
        content += next(infer(
            "Input: " + input,
            mem=[],
            modelname='Output:\n<startfunc>\n[{\n  "function": "',
            system=f"You are an AI assistant named GateKeeper, The current date is {datetime.now()}, please select the single most suitable function and parameters from the list of available functions below, based on the user's input and pay attention to the context, which will then be passed over to polymind. Provide your response in JSON format surrounded by '<startfunc>' and '<endfunc>' without any notes, comments or follow-ups. Only JSON.\n{funclist}",
            temperature=0.1,
            top_p=0.1,
            min_p=0.05,
            top_k=40,
            stopstrings=[
                "Input: ",
                "[INST]",
                "[/INST]",
                "```",
                "</s>",
                "user:",
                "polymind:",
                "Polymind:",
                "<</SYS>>",
                "[System Message]",
                "endfunc",
                "<endfunc>",
                "}<",
                "</startfunc>",
            ],
            max_tokens=500,
        ))[0]

    try:
        if "<startfunc>" in content:
            content = content.split("<startfunc>")[1]
        content = (
            re.sub(r"\\_", "_", html.unescape(content))
            .replace("\\_", "_")
            .replace("}<", "}")
            .replace("<startfunc>", "")
            .replace("</", "")
            .replace("<", "")
        )
        print(content)
        result = ""

        for x in json.loads(content.replace("Output:", "")):
            if stream:
                yield {"result": x, "type": "func"}

            if x['function'] == "searchfile" and Shared_vars.config.enabled_features['file_input']['raw_input']:
                if 'params' in x:
                    x['params']['query'] = input 
                elif 'parameters' in x:
                    x['parameters']['query'] = input 
                else:
                    x['query'] = input

            run = Util(x, ip, depth)
            if run != "null":
                result += run
        if stream:
            result = result if result != "" else "null" 
            result = {"result": result, "type": "result"}
            yield result
        else:
            return result if result != "" else "null"
    except Exception as e:
        print(e)
        if stream:
            yield {"result": "null", "type": "result"}
        else:
            return "null"


def Util(rsp, ip, depth):
    result = ""

    rsp["function"] = (
        re.sub(r"\\_", "_", html.unescape(rsp["function"]))
        .replace("\\_", "_")
        .replace("{<", "{")
        .replace("<startfunc>", "")
    )
    params = rsp['params'] if 'params' in rsp else (rsp['parameters'] if 'parameters' in rsp else rsp)

    if rsp["function"] == "acknowledge":
        return "null"

    elif rsp["function"] == "clearmemory":
        Shared_vars.mem[f"{ip}"] = []
        Shared_vars.vismem[f"{ip}"] = []
        if ip in Shared_vars.loadedfile:
            Shared_vars.loadedfile[ip] = {}
        return "skipment{<" + params["message"]

    elif rsp["function"] == "updateconfig":
        if ip != Shared_vars.config.adminip:
            return "null"
        check = False if params["option"].split(":")[1].lower() == "false" else True
        Shared_vars.config.enabled_features[params["option"].split(":")[0]][
            "enabled"
        ] = check
        result = f"{params['option'].split(':')[0]} is now set to {Shared_vars.config.enabled_features[params['option'].split(':')[0]]['enabled']}"
        print(result)
        return result

    elif rsp["function"] == "wolframalpha":
        if Shared_vars.config.enabled_features["wolframalpha"]["enabled"] == False:
            return "Wolfram Alpha is currently disabled."
        try:
            res = client.query(params["query"])
            results = ""
            checkimage = False
            for pod in res.pods:
                for sub in pod.subpods:
                    if (
                        "plot"
                        or "image" in sub.img["@alt"].lower()
                        and "plot |" not in sub.img["@alt"].lower()
                    ) and get_image_size(sub.img["@src"]) > 350:
                        results += (
                            f'<img src="{sub.img["@src"]}" alt="{sub.img["@alt"]}"/>'
                            + "\n"
                        )
                        checkimage = True
                    elif sub.plaintext:
                        results += sub.plaintext + "\n"
            if results == "":
                result = "No results from Wolfram Alpha."
            else:
                result = "Wolfram Alpha result: " + results
            if checkimage:
                result += "\nREMINDER: ALWAYS include the provided graph/plot images in the provided format in your explanation if theres any when explaining the results in a short and concise manner."
            print(result)
            return result
        except Exception as e:
            return "Wolfram Alpha Error: " + str(e)

    elif rsp["function"] == "generateimage":
        if Shared_vars.config.enabled_features["imagegeneration"]["enabled"] == False:
            return "Image generation is currently disabled."
        return imagegen(params["prompt"])

    elif rsp["function"] == "searchfile":
        file = Shared_vars.loadedfile[ip]
        searchinput = params["query"]
        print(f"Using query: {searchinput}")
        return f"<FILE_CHUNK {queryEmbeddings(searchinput, file[0], file[1])[1]} >"

    elif rsp["function"] == "runpythoncode":
        if Shared_vars.config.enabled_features["runpythoncode"]["enabled"] == False:
            return "Python code execution is currently disabled."
        if ip != Shared_vars.config.adminip:
            return "null"
        time.sleep(5)
        checkstring = ""
        ocode = params["code"]
        if "plt.show()" in params["code"]:
            params["code"] = re.sub('print\s*\(.*\)', '', params["code"])
            plotb64 = """import io\nimport base64\nbyt = io.BytesIO()\nplt.savefig(byt, format='png')\nbyt.seek(0)\nprint(f'data:image/png;base64,{base64.b64encode(byt.read()).decode()}',end="")"""
            params["code"] = params["code"].replace("plt.show()", plotb64)

        output = subprocess.run(
            ["python3", "-c", params["code"]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = output.stdout.decode(), output.stderr.decode()
        if (
            stderr != ""
            and depth < Shared_vars.config.enabled_features["runpythoncode"]["depth"]
        ):
            print(f"Current depth: {depth}")
            return next(GateKeep(
                f"```{ocode}```\n The above code produced the following error\n{stderr}\n Rewrite the code to solve the error and run the fixed code.",
                ip,
                depth + 1,
            ))
        if "data:image/png;base64," in stdout:
            checkstring = "{<plotimg;" + stdout
            print(
                f"CompletedProcess(args=['python3', '-c', {ocode}], stdout='<image>', stderr={stderr}"
            )
        else:
            print(output)
        result = (
            f"Code to be ran: \n```{params['code']}```\n<Code interpreter output>:\nstdout: {stdout}\nstderr: {stderr}\n<\Code interpreter output>"
            if checkstring == ""
            else f"Code to be ran: \n```{ocode}```\n<Code interpreter output>:\nstdout:\nstderr: {stderr}\n<\Code interpreter output>{checkstring}"
        )
        return result

    elif rsp["function"] == "internetsearch":
        if Shared_vars.config.enabled_features["internetsearch"]["enabled"] == False:
            return "Internet search is currently disabled."
        with DDGS() as ddgs:
            for r in ddgs.text(params["keywords"], safesearch="Off", max_results=4):
                title = r["title"]
                link = r["href"]
                result += f' *Title*: {title} *Link*: {link} *Body*: {r["body"]}\n*Scraped_text*: {scrape_site(link, 700)}'
        return "<Search results>:\n" + result

    elif rsp["function"] == "portscan":
        if ip != Shared_vars.config.adminip:
            return "null"
        nm = nmap.PortScanner()
        try:
            nm.scan(params["ip"])
            if nm[params["ip"]].state() == "up":
                for x in nm[params["ip"]]["tcp"].keys():
                    result += f"{nm[rsp['params']['ip']]['tcp'][x]['name']}: State {nm[rsp['params']['ip']]['tcp'][x]['state']} ({x})\n"
                return f"<Portscan output for IP {rsp['params']['ip']}>: " + result
        except:
            return f"<Portscan output for IP {rsp['params']['ip']}>: Host down."

    return "null"
