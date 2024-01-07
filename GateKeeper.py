from openai import OpenAI
import os
import json
import re
import html
import time
from duckduckgo_search import DDGS
import nmap
import subprocess
import Shared_vars
from comfyui import imagegen
from inference import infer
import traceback
from scrape import scrape_site

path = os.path.realpath(__file__).strip("GateKeeper.py")
client = OpenAI(
    base_url=f"http://{Shared_vars.config.host}:{Shared_vars.config.port}/v1",
    api_key=Shared_vars.config.api_key,
)
func = ""

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


def GateKeep(input, ip):
    content = ""
    print("Begin streamed GateKeeper output.")
    examplefnc = '<startfunc>{\n"function": "internetsearch",\n"params": {\n"keywords": "mixtral"\n}\n}<endfunc>'
    fewshot = f"""{Shared_vars.config.llm_parameters['beginsep']} Input:\nDescribe the model mixtral.{Shared_vars.config.llm_parameters['endsep']}{examplefnc}"""
    try:
        ctxstr = ""
        for x in Shared_vars.vismem[f"{ip}"][-2:]:
            ctxstr += "USER: " + x["user"] + "\n" + "PolyMind: " + x["assistant"]
        content = infer(
            "Input: " + input,
            mem=[],
            modelname="Output:",
            system=f"You are an AI assistant named GateKeeper, please select the single most suitable function and parameters from the list of available functions below, based on the user's input and pay attention to the context, which will then be passed over to polymind. Provide your response in JSON format surrounded by '<startfunc>' and '<endfunc>' without any notes, comments or follow-ups. Only JSON.\n{func}\nContext: {ctxstr}\n",
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
        )[0]
    except TypeError:
        content = infer(
            "Input: " + input,
            mem=[],
            modelname="Output:",
            system=f"You are an AI assistant named GateKeeper, please select the single most suitable function and parameters from the list of available functions below, based on the user's input and pay attention to the context, which will then be passed over to polymind. Provide your response in JSON format surrounded by '<startfunc>' and '<endfunc>' without any notes, comments or follow-ups. Only JSON.\n{func}",
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
    except Exception as e:
        return "null"


def Util(rsp, ip):
    result = ""

    rsp["function"] = (
        re.sub(r"\\_", "_", html.unescape(rsp["function"]))
        .replace("\\_", "_")
        .replace("{<", "{")
        .replace("<startfunc>", "")
    )
    if rsp["function"] == "acknowledge":
        return "null"

    elif rsp["function"] == "clearmemory":
        Shared_vars.mem[f"{ip}"] = []
        Shared_vars.vismem[f"{ip}"] = []
        return "skipment{<" + rsp["params"]["message"]

    elif rsp["function"] == "generateimage":
        return imagegen(rsp["params"]["prompt"])
    elif rsp["function"] == "runpythoncode":
        if ip != Shared_vars.config.adminip:
            return "null"
        time.sleep(5)
        output = subprocess.run(
            ["python3", "-c", rsp["params"]["code"]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(output)
        stdout, stderr = output.stdout.decode(), output.stderr.decode()
        return f"Code to be ran: \n```{rsp['params']['code']}```\n<Code interpreter output>:\nstdout: {stdout}\nstderr: {stderr}\n<\Code interpreter output>"

    elif rsp["function"] == "internetsearch":
        with DDGS() as ddgs:
            for r in ddgs.text(
                rsp["params"]["keywords"], safesearch="Off", max_results=4
            ):
                title = r["title"]
                link = r["href"]
                result += f' *Title*: {title} *Link*: {link} *Body*: {r["body"]}\n*Scraped_text*: {scrape_site(link, 700)}'
        return "<Search results>:\n" + result

    elif rsp["function"] == "portscan":
        if ip != Shared_vars.config.adminip:
            return "null"
        nm = nmap.PortScanner()
        try:
            nm.scan(rsp["params"]["ip"])
            if nm[rsp["params"]["ip"]].state() == "up":
                for x in nm[rsp["params"]["ip"]]["tcp"].keys():
                    result += f"{nm[rsp['params']['ip']]['tcp'][x]['name']}: State {nm[rsp['params']['ip']]['tcp'][x]['state']} ({x})\n"
                return f"<Portscan output for IP {rsp['params']['ip']}>: " + result
        except:
            return f"<Portscan output for IP {rsp['params']['ip']}>: Host down."

    return "null"
