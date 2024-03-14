import json
import random
import Shared_vars
import requests
import traceback
if Shared_vars.config.compat:
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(Shared_vars.config.tokenmodel)

API_ENDPOINT_URI = Shared_vars.API_ENDPOINT_URI
API_KEY = Shared_vars.API_KEY
TABBY = Shared_vars.TABBY
if TABBY:
    API_ENDPOINT_URI += "v1/completions"
else:
    API_ENDPOINT_URI += "completion"


def tokenize(input):
    if Shared_vars.config.compat:
        encoded_input = tokenizer.encode(input, return_tensors=None)
        tokens = tokenizer.convert_ids_to_tokens(encoded_input)
        return {"length": len(encoded_input), "tokens": tokens}
    else:
        if TABBY:
            payload = {
                "add_bos_token": "true",
                "encode_special_tokens": "true",
                "decode_special_tokens": "true",
                "text": input,
            }
            request = requests.post(
                API_ENDPOINT_URI.replace("completions", "token/encode"),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}",
                },
                json=payload,
                timeout=360,
            )
            return request.json()
        else:
            payload = {"content": input}
            request = requests.post(
                API_ENDPOINT_URI.replace("completion", "tokenize"),
                json=payload,
                timeout=360,
            )
            return {"length": len(request.json()["tokens"])}


def infer(
    prmpt,
    system="",
    temperature=0.7,
    username="",
    bsysep=Shared_vars.config.llm_parameters["bsysep"],
    esysep=Shared_vars.config.llm_parameters["esysep"],
    modelname="",
    eos="</s><s>",
    beginsep=Shared_vars.config.llm_parameters["beginsep"],
    endsep=Shared_vars.config.llm_parameters["endsep"],
    mem=[],
    few_shot="",
    max_tokens=250,
    stopstrings=[],
    top_p=1.0,
    top_k=Shared_vars.config.llm_parameters["top_k"],
    min_p=0.0,
    streamresp=False,
    reppenalty=Shared_vars.config.llm_parameters["repetition_penalty"] if "repetition_penalty" in Shared_vars.config.llm_parameters else 1.0,
    max_temp=Shared_vars.config.llm_parameters["max_temp"] if "max_temp" in Shared_vars.config.llm_parameters else 0,
    min_temp=Shared_vars.config.llm_parameters["min_temp"] if "min_temp" in Shared_vars.config.llm_parameters else 0
):
    content = ""
    memory = mem
    prompt = (
        f"{bsysep}\n"
        + system
        + f"\n{esysep}\n"
        + few_shot
        + "".join(memory)
        + f"\n{beginsep} {username} {prmpt}{endsep} {modelname}"
    )
    # This feels wrong.

    print(f"Token count: {tokenize(prompt)['length']}")
    removal = 0
    while (
        tokenize(prompt)["length"] + max_tokens / 2 > Shared_vars.config.ctxlen
        and len(memory) > 2
    ):
        print(f"Removing old memories: Pass:{removal}")
        removal += 1
        memory = memory[removal:]
        prompt = (
            f"{bsysep}\n"
            + system
            + f"\n{esysep}\n"
            + few_shot
            + "".join(memory)
            + f"\n{beginsep} {username} {prmpt} {endsep} {modelname}"
        )
    stopstrings += ["</s>", "<</SYS>>", "[Inst]", "[/INST]", Shared_vars.config.llm_parameters["bsysep"], Shared_vars.config.llm_parameters["esysep"], Shared_vars.config.llm_parameters["beginsep"], Shared_vars.config.llm_parameters["endsep"]]
    payload = {
        "prompt": prompt,
        "model": "gpt-3.5-turbo-instruct",
        "max_tokens": max_tokens,
        "n_predict": max_tokens,
        "min_p": min_p,
        "repetition_penalty": reppenalty,
        "stream": True,
        "seed": random.randint(
            1000002406736107, 3778562406736107
        ),  # Was acting weird without this
        "top_k": top_k,
        "top_p": top_p,
        "stop": [beginsep] +  stopstrings,
        "temperature": temperature,
    }
    if min_temp != 0 and max_temp != 0:
        payload["min_temp"] = min_temp
        payload["max_temp"] = max_temp
    request = requests.post(
        API_ENDPOINT_URI,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        json=payload,
        stream=True,
        timeout=360,
    )

    if request.encoding is None:
        request.encoding = "utf-8"
    prevtoken = ""
    repetitioncount = 0
    for line in request.iter_lines(decode_unicode=True):
        if line:
            if TABBY:
                try:
                    if " ".join(line.split(" ")[1:]) != "[DONE]":
                        if (
                            prevtoken
                            == json.loads(" ".join(line.split(" ")[1:]))["choices"][0][
                                "text"
                            ]
                        ):
                            repetitioncount += 1
                            if repetitioncount > 25:
                                print("Stopping loop due to repetition")
                                break
                        else:
                            repetitioncount = 0
                        prevtoken = json.loads(" ".join(line.split(" ")[1:]))["choices"][0][
                            "text"
                        ]
                        print(
                            json.loads(" ".join(line.split(" ")[1:]))["choices"][0]["text"],
                            end="",
                            flush=True,
                        )
                        if streamresp:
                            yield json.loads(" ".join(line.split(" ")[1:]))["choices"][0][
                                "text"
                            ]

                        content += json.loads(" ".join(line.split(" ")[1:]))["choices"][0][
                            "text"
                        ]
                except Exception:
                    pass
            else:
                try:
                    if "data" in line:
                        print(
                            json.loads(" ".join(line.split(" ")[1:]))["content"],
                            end="",
                            flush=True,
                        )
                        if (
                            prevtoken
                            == json.loads(" ".join(line.split(" ")[1:]))["content"]
                        ):
                            repetitioncount += 1
                        if repetitioncount > 25:
                            print("Stopping loop due to repetition")
                            break
                        else:
                            repetitioncount = 0
                        prevtoken = json.loads(" ".join(line.split(" ")[1:]))["content"]
                        if streamresp:
                            yield json.loads(" ".join(line.split(" ")[1:]))["content"]

                        content += json.loads(" ".join(line.split(" ")[1:]))["content"]

                except Exception:
                    print(traceback.format_exc())
    print("")
    memory.append(
        f"\n{beginsep} {username} {prmpt.strip()}\n{endsep} {modelname} {content.strip()}{eos}"
    )

    yield [content, memory, tokenize(prompt)["length"]]
