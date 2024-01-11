from openai import OpenAI
import os
import json
import re
import html
import time
import wolframalpha
from duckduckgo_search import DDGS
import nmap
from datetime import datetime
import subprocess
import Shared_vars
from comfyui import imagegen
from inference import infer
from scrape import scrape_site
import requests
from PIL import Image
from io import BytesIO

path = os.path.realpath(__file__).strip("GateKeeper.py")
client = OpenAI(
    base_url=f"http://{Shared_vars.config.host}:{Shared_vars.config.port}/v1",
    api_key=Shared_vars.config.api_key,
)
func = ""
client = wolframalpha.Client(
    Shared_vars.config.enabled_features["wolframalpha"]["app_id"]
)

with open(path + "functions.json") as user_file:
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
        func += template


def get_image_size(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img.size[0] + img.size[1]


def GateKeep(input, ip):
    content = ""
    print("Begin streamed GateKeeper output.")
    examplefnc = '<startfunc>{\n"function": "internetsearch",\n"params": {\n"keywords": "mixtral"\n}\n}<endfunc>'
    fewshot = f"""{Shared_vars.config.llm_parameters['beginsep']} Input:\nDescribe the model mixtral.{Shared_vars.config.llm_parameters['endsep']}{examplefnc}"""
    try:
        ctxstr = ""
        for x in Shared_vars.vismem[f"{ip}"][-2:]:
            ctxstr += re.sub(
                r"!\[.*?\]\(.*?\)|<img.*?>",
                "",
                "USER: " + x["user"] + "\n" + "PolyMind: " + x["assistant"],
            )
        content = "<startfunc>\n{"
        content += infer(
            "Input: " + input,
            mem=[],
            modelname="Output:\n<startfunc>\n{",
            system=f"You are an AI assistant named GateKeeper, The current date is {datetime.now()}, please select the single most suitable function and parameters from the list of available functions below, based on the user's input and pay attention to the context, which will then be passed over to polymind. Provide your response in JSON format surrounded by '<startfunc>' and '<endfunc>' without any notes, comments or follow-ups. Only JSON.\n{func}\nContext: {ctxstr}\n",
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
        )[0]
    except TypeError:
        content = "<startfunc>\n{"
        content += infer(
            "Input: " + input,
            mem=[],
            modelname="Output:\n<startfunc>\n{",
            system=f"You are an AI assistant named GateKeeper, The current date is {datetime.now()}, please select the single most suitable function and parameters from the list of available functions below, based on the user's input and pay attention to the context, which will then be passed over to polymind. Provide your response in JSON format surrounded by '<startfunc>' and '<endfunc>' without any notes, comments or follow-ups. Only JSON.\n{func}",
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
        )[0]

    try:
        if "<startfunc>" in content:
            content = content.split("<startfunc>")[1]
        content = (
            re.sub(r"\\_", "_", html.unescape(content))
            .replace("\\_", "_")
            .replace("}<", "}")
            .replace("<startfunc>", "")
            .replace("<", "")
            .replace("/", "")
        )
        print(content)
        return Util(json.loads(content.replace("Output:", "")), ip)
    except Exception:
        return "null"


def Util(rsp, ip):
    result = ""

    rsp["function"] = (
        re.sub(r"\\_", "_", html.unescape(rsp["function"]))
        .replace("\\_", "_")
        .replace("{<", "{")
        .replace("<startfunc>", "")
    )
    params = rsp["params"] if "params" in rsp else rsp

    if rsp["function"] == "acknowledge":
        return "null"

    elif rsp["function"] == "clearmemory":
        Shared_vars.mem[f"{ip}"] = []
        Shared_vars.vismem[f"{ip}"] = []
        return "skipment{<" + params["message"]
    
    elif rsp["function"] == "updateconfig":
        if ip != Shared_vars.config.adminip:
            return "null"
        check = False if params['option'].split(":")[1].lower() == "false" else True
        Shared_vars.config.enabled_features[params['option'].split(":")[0]]["enabled"] = check
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
                result += "\nREMINDER: ALWAYS include the provided graph/plot images in your explanation if theres any when explaining the results in a short and concise manner."
            print(result)
            return result
        except Exception as e:
            return "Wolfram Alpha Error: " + str(e)

    elif rsp["function"] == "generateimage":
        if Shared_vars.config.enabled_features["imagegeneration"]["enabled"] == False:
            return "Image generation is currently disabled."
        return imagegen(params["prompt"])
    elif rsp["function"] == "runpythoncode":
        if Shared_vars.config.enabled_features["runpythoncode"]["enabled"] == False:
            return "Python code execution is currently disabled."
        if ip != Shared_vars.config.adminip:
            return "null"
        time.sleep(5)
        checkstring = ""
        if "plt.show()" in params["code"]:
            plotb64 = """import io\nimport base64\nbyt = io.BytesIO()\nplt.savefig(byt, format='png')\nbyt.seek(0)\nprint(f'data:image/png;base64,{base64.b64encode(byt.read()).decode()}',end="")"""
            ocode = params["code"]
            params["code"] = params["code"].replace("plt.show()", plotb64)

        output = subprocess.run(
            ["python3", "-c", params["code"]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(output)
        stdout, stderr = output.stdout.decode(), output.stderr.decode()
        if "data:image/png;base64," in stdout:
            checkstring = "{<plotimg;" + stdout
        result = (
            f"Code to be ran: \n```{rsp['params']['code']}```\n<Code interpreter output>:\nstdout: {stdout}\nstderr: {stderr}\n<\Code interpreter output>"
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
