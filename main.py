from flask import Flask, render_template, request, jsonify, Response
from GateKeeper import GateKeep, infer
from Shared import Adapters
import datetime
import Shared_vars
import io
import base64
import time
import json
from PIL import Image
import html

if Shared_vars.config.enabled_features["file_input"]["enabled"]:
    from FileHandler import handleFile
if Shared_vars.config.enabled_features["image_input"]["enabled"]:
    from ImageRecognition import identify
import re


def create_thumbnail(image_data, size=(512, 512)):
    img = Image.open(io.BytesIO(base64.b64decode(image_data)))
    img.thumbnail(size, Image.LANCZOS)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue())
    return f"data:image/jpeg;base64,{img_str.decode()}"


def convert_to_html_code_block(markdown_text):
    # Regex pattern to match code blocks
    pattern = r"```(.*?)```"

    # Function to convert matched code block to HTML
    def replacer(match):
        code_block = match.group(1)
        html_code_block = f"<pre><code>{code_block}</code></pre>"
        return html_code_block

    # Replace all code blocks in the text
    html_text = re.sub(pattern, replacer, markdown_text, flags=re.DOTALL)

    return html_text


chosenfunc = {}
currenttoken = {}

app = Flask(__name__)
today = datetime.date.today()


@app.route("/stream")
def stream():
    def generate():
        while True:
            yield f"data: {json.dumps(chosenfunc)}\n\n"
            yield f"data: {json.dumps(currenttoken)}\n\n"
            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")


@app.route("/remove_message", methods=["POST"])
def remove_message():
    data = request.get_json()
    index = data.get("index")
    try:
        del Shared_vars.vismem[f"{request.remote_addr}"][index]
        del Shared_vars.mem[f"{request.remote_addr}"][index]
        return jsonify({"status": "success"}), 200
    except IndexError:
        return jsonify({"status": "error", "message": "Invalid index"}), 400


@app.route("/", methods=["GET", "POST"])
def chat():
    global chosenfunc
    global currenttoken
    try:
        chosenfunc[f"{request.remote_addr}"]["ip"] = request.remote_addr
        test = Shared_vars.mem[f"{request.remote_addr}"]
        test = Shared_vars.vismem[f"{request.remote_addr}"]
    except KeyError:
        print("initializing memory")
        chosenfunc[f"{request.remote_addr}"] = {"func": "", "ip": ""}
        Shared_vars.mem[f"{request.remote_addr}"] = []
        Shared_vars.vismem[f"{request.remote_addr}"] = []

    if request.method == "POST":
        if request.form.get("user"):
            username = request.form.get("user") + ":"
        else:
            username = "user:"
        user_input = request.form.get("input")
        answers = Adapters(user_input)
        Kept = ""
        for y in GateKeep(answers, request.remote_addr, stream=True):
            if y["type"] == "func":
                try:
                    chosenfunc[f"{request.remote_addr}"]["func"] = y["result"][
                        "function"
                    ]
                except Exception:
                    chosenfunc[f"{request.remote_addr}"]["func"] = ""
            else:
                Kept = y["result"]
        newinp = ""
        imgstr = ""
        genedimage = False
        if "[<image>" in Kept:
            prmpt = Kept.split("[<image>")[0]
            newinp += (
                answers.strip()
                + f"\nSYSTEM: Image generated with Stable Diffusion and sent to user succesfully. Prompt: {prmpt}\nREMINDER: NEVER Tell the user you are not capable of generating images, instead mention the image was generated as requested and optionally mention the prompt. Do not include an example link nor a note."
            )
            Kept = Kept.replace(prmpt, "")
            genedimage = True
            oimg = Kept.replace("[", "").replace("]", "").split("<image>")[1]
            img = create_thumbnail(
                Kept.replace("[", "").replace("]", "").split("<image>")[1]
            )

            Kept = re.sub(r"\[<image>.*?<image>\]", "", Kept)
        elif (
            Kept != "null"
            and Kept
            and "skipment" not in Kept
            and "plotimg" not in Kept
            and "[<image>" not in Kept
        ):
            newinp += answers.strip() + "\nSYSTEM: " + Kept
        elif "skipment" in Kept:
            currenttoken[f"{request.remote_addr}"] = {
                "func": "",
                "ip": f"{request.remote_addr}",
                "token": Kept.split("{<")[1].replace("<", "&lt;").replace(">", "&gt;")
                + "</s><s>",
            }
            return jsonify(
                {
                    "output": Kept.split("{<")[1]
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                }
            )
        if "{<plotimg;" in Kept:
            newinp = answers.strip()
            newinp += Kept.split("{<plotimg;")[0]
            oimg = Kept.split("{<plotimg;")[1]
            imgstr = Kept.split("{<plotimg;")[1]
        if Kept == "null":
            newinp = ""
            newinp += answers.strip()

        complete = ["", []]

        for tok in infer(
            newinp,
            system=f"{Shared_vars.config.system}\nThe current date is {today}",
            mem=Shared_vars.mem[f"{request.remote_addr}"],
            username=username,
            modelname="polymind:",
            max_tokens=Shared_vars.config.llm_parameters['max_new_tokens'],
            temperature=Shared_vars.config.llm_parameters["temperature"],
            top_p=1,
            min_p=Shared_vars.config.llm_parameters["min_p"],
            stopstrings=[
                "user:",
                "polymind:",
                "[System Message]",
                "<|im_end|>",
                "<|im_start|>",
                "SYSTEM:",
                '<img src="data:image/jpeg;base64,',
                '<|endoftext|>',
                '[FINISHED]',
                'User:',
                'Polymind:',
                '<disclaimer>',
                '</disclaimer>'
            ],
            streamresp=True,
            few_shot=Shared_vars.config.llm_parameters['fewshot']
        ):
            if type(tok) != list:
                complete[0] += tok
                currenttoken[f"{request.remote_addr}"] = {
                    "func": "",
                    "ip": f"{request.remote_addr}",
                    "token": complete[0],
                }
            else:
                complete[1] = tok[1]
                if complete[0].count('```') == 1:
                    complete[0] = complete[0].replace("```", '')
                currenttoken[f"{request.remote_addr}"] = {
                    "func": "",
                    "ip": f"{request.remote_addr}",
                    "token": complete[0]
                    + "</s><s>",
                }
        Shared_vars.mem[f"{request.remote_addr}"] = complete[1]
        Shared_vars.vismem[f"{request.remote_addr}"].append(
            {
                "user": user_input,
                "assistant": complete[0]
            }
        )

        chosenfunc[f"{request.remote_addr}"]["func"] = ""
        if genedimage:
            return jsonify(
                {
                    "output": complete[0],
                    "base64_image": img,
                    "base64_image_full": oimg,
                    "index": len(Shared_vars.vismem[f"{request.remote_addr}"]) - 1,
                }
            )
        elif imgstr != "":
            return jsonify(
                {
                    "output": complete[0],
                    "base64_image": imgstr,
                    "base64_image_full": oimg,
                    "index": len(Shared_vars.vismem[f"{request.remote_addr}"]) - 1,
                }
            )
        else:
            return jsonify(
                {
                    "output": complete[0],
                    "index": len(Shared_vars.vismem[f"{request.remote_addr}"]) - 1,
                }
            )
    else:
        return render_template("chat.html", user_ip=request.remote_addr)


@app.route("/chat_history", methods=["GET"])
def chat_history():
    return Shared_vars.vismem[f"{request.remote_addr}"]


@app.route("/upload_file", methods=["POST"])
def upload_file():
    global chosenfunc
    if request.method == "POST" and (
        Shared_vars.config.enabled_features["image_input"]["enabled"]
        or Shared_vars.config.enabled_features["file_input"]["enabled"]
    ):
        if not f"{request.remote_addr}" in Shared_vars.mem or not f"{request.remote_addr}" in Shared_vars.vismem:
            Shared_vars.mem[f"{request.remote_addr}"] = []
            Shared_vars.vismem[f"{request.remote_addr}"] = []

        imgstr = ""
        file = request.files["file"]
        file_content = request.form["content"]
        if (
            ".jpg" in file.filename
            or ".png" in file.filename
            or ".jpeg" in file.filename
            or ".png" in file.filename
        ) and Shared_vars.config.enabled_features["image_input"]["enabled"]:
            if f"{request.remote_addr}" in chosenfunc:
                chosenfunc[f"{request.remote_addr}"]["func"] = "procimg"
            else:
                chosenfunc[f"{request.remote_addr}"] = {
                    "func": "procimg",
                    "ip": f"{request.remote_addr}",
                }
            result = identify(file_content.split(',')[1])
            
            Shared_vars.mem[f"{request.remote_addr}"].append(
                f"\n{Shared_vars.config.llm_parameters['beginsep']} user: {result} {Shared_vars.config.llm_parameters['endsep']}"
            )
            Shared_vars.vismem[f"{request.remote_addr}"].append({"user": result})
            return jsonify(
                {
                    "base64_image": create_thumbnail(
                        file_content.split(",")[1], size=(256, 256)
                    )
                }
            )
        elif Shared_vars.config.enabled_features["file_input"]["enabled"]:
            if f"{request.remote_addr}" in chosenfunc:
                chosenfunc[f"{request.remote_addr}"]["func"] = "loadembed"
            else:
                chosenfunc[f"{request.remote_addr}"] = {
                    "func": "loadembed",
                    "ip": f"{request.remote_addr}",
                }
            chunks = handleFile(file_content)
            if len(chunks) <= 1:
                Shared_vars.loadedfile[f"{request.remote_addr}"] = {}
                Shared_vars.mem[f"{request.remote_addr}"].append(
                    f"\n{Shared_vars.config.llm_parameters['beginsep']} user: <FILE {file.filename}> {chunks[0]} {Shared_vars.config.llm_parameters['endsep']}"
                )
            else:
                Shared_vars.loadedfile[f"{request.remote_addr}"] = chunks
            chosenfunc[f"{request.remote_addr}"]["func"] = ""

        return jsonify({"message": f"{file.filename} uploaded successfully."})


if __name__ == "__main__":
    port = 5000
    if Shared_vars.config.port == port:
        port = 8750
    app.run(host=Shared_vars.address, port=port)
