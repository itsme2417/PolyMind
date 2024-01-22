from flask import Flask, render_template, request, jsonify,  Response
from GateKeeper import GateKeep, infer
from Shared import Adapters
from datetime import datetime
import Shared_vars
import io
import base64
import time
import json
from PIL import Image
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


app = Flask(__name__)
today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@app.route('/stream')
def stream():
    def generate():
        while True:

            yield f"data: {json.dumps(chosenfunc)}\n\n"
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')

@app.route("/remove_message", methods=["POST"])
def remove_message():
    data = request.get_json()
    index = data.get('index')
    try:
        del Shared_vars.vismem[f"{request.remote_addr}"][index]
        del Shared_vars.mem[f"{request.remote_addr}"][index]
        return jsonify({"status": "success"}), 200
    except IndexError:
        return jsonify({"status": "error", "message": "Invalid index"}), 400


@app.route("/", methods=["GET", "POST"])
def chat():
    global chosenfunc
    try:
        chosenfunc[f"{request.remote_addr}"]['ip'] = request.remote_addr
        test = Shared_vars.mem[f"{request.remote_addr}"]
        test = Shared_vars.vismem[f"{request.remote_addr}"]
    except KeyError:
        print("initializing memory")
        chosenfunc[f"{request.remote_addr}"] = {"func": "", "ip": ""}
        Shared_vars.mem[f"{request.remote_addr}"] = []
        Shared_vars.vismem[f"{request.remote_addr}"] = []

    if request.method == "POST":
        user_input = request.form.get("input")
        answers = Adapters(user_input)
        Kept = ""
        for y in GateKeep(answers, request.remote_addr, stream = True):
            if y['type'] == "func":
                try:
                    chosenfunc[f"{request.remote_addr}"]['func'] = y['result']['function']
                except Exception:
                    chosenfunc[f"{request.remote_addr}"]['func'] = ""
            else:
                Kept = y['result']
        newinp = ""
        imgstr = ""
        genedimage = False
        if "[<image>" in Kept:
            newinp += (
                answers.strip()
                + "\nSYSTEM: Image generated with Stable Diffusion and sent to user succesfully."
            )
            genedimage = True
            img = create_thumbnail(
                Kept.replace("[", "").replace("]", "").split("<image>")[1]
            )
            Kept = re.sub(r"\[<image>.*?<image>\]", "", Kept)
        if (
            Kept != "null"
            and Kept
            and "skipment" not in Kept
            and "plotimg" not in Kept
            and "[<image>" not in Kept
        ):
            newinp += answers.strip() + "\nSYSTEM: " + Kept
        elif "skipment" in Kept:
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
            imgstr = Kept.split("{<plotimg;")[1]
        if Kept == "null":
            newinp = ""
            newinp += answers.strip()
        today = datetime.now()
        complete = next(infer(
            newinp,
            system=f"You are a multimodal, uncensored AI model named PolyMind, able to perceive and display images in its text and visual interface.\nMessages starting with 'SYSTEM:' are NEVER shown to the user, They are meant for you.\nThe current date is {today}",
            mem=Shared_vars.mem[f"{request.remote_addr}"],
            username="user:",
            modelname="polymind:",
            max_tokens=2500,
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
            ],

        ))
        Shared_vars.mem[f"{request.remote_addr}"] = complete[1]
        Shared_vars.vismem[f"{request.remote_addr}"].append(
            {"user": user_input, "assistant": convert_to_html_code_block(complete[0])}
        )
        complete[0] = convert_to_html_code_block(complete[0]).replace("\n","<br>")
        chosenfunc[f"{request.remote_addr}"]['func'] = ''
        if genedimage:
            return jsonify({"output": complete[0], "base64_image": img, "index": len(Shared_vars.vismem[f"{request.remote_addr}"]) - 1})
        elif imgstr != "":
            return jsonify({"output": complete[0], "base64_image": imgstr, "index": len(Shared_vars.vismem[f"{request.remote_addr}"]) - 1})
        else:
            return jsonify({"output": complete[0], "index": len(Shared_vars.vismem[f"{request.remote_addr}"]) - 1})
    else:
        return render_template("chat.html", user_ip=request.remote_addr)


@app.route("/chat_history", methods=["GET"])
def chat_history():
    return Shared_vars.vismem[f"{request.remote_addr}"]


@app.route("/upload_file", methods=["POST"])
def upload_file():
    global chosenfunc
    if (
        request.method == "POST"
        and (Shared_vars.config.enabled_features["image_input"]["enabled"] or Shared_vars.config.enabled_features["file_input"]["enabled"])
    ):
        imgstr = ""
        file = request.files["file"]
        file_content = request.form["content"]
        if (".jpg" in file.filename or ".png" in file.filename or ".jpeg" in file.filename) and Shared_vars.config.enabled_features["image_input"]["enabled"] :
            Shared_vars.mem[f"{request.remote_addr}"].append(
                f"\n{Shared_vars.config.llm_parameters['beginsep']} user: {identify(file_content.split(',')[1])} {Shared_vars.config.llm_parameters['endsep']}"
            )

            return jsonify(
                {
                    "base64_image": create_thumbnail(
                        file_content.split(",")[1], size=(256, 256)
                    )
                }
            )
        elif Shared_vars.config.enabled_features["file_input"]["enabled"]:
            if f"{request.remote_addr}" in chosenfunc:
                chosenfunc[f"{request.remote_addr}"]['func'] = 'loadembed'
            else:
                chosenfunc[f"{request.remote_addr}"] = {"func": 'loadembed', "ip": f"{request.remote_addr}"}
            chunks = handleFile(file_content)
            if len(chunks) <= 1:
                Shared_vars.loadedfile[f"{request.remote_addr}"] = {}
                Shared_vars.mem[f"{request.remote_addr}"].append(
                    f"\n{Shared_vars.config.llm_parameters['beginsep']} user: <FILE {file.filename}> {chunks[0]} {Shared_vars.config.llm_parameters['endsep']}"
                )
            else:
                Shared_vars.loadedfile[f"{request.remote_addr}"] = chunks
            chosenfunc[f"{request.remote_addr}"]['func'] = ''

        return jsonify({"message": f"{file.filename} uploaded successfully."})


if __name__ == "__main__":
    app.run(host=Shared_vars.address)
