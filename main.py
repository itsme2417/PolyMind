from flask import Flask, render_template, request, jsonify
from GateKeeper import GateKeep, infer
from Shared import Adapters
from datetime import datetime
import Shared_vars
import io
import base64
from PIL import Image
if Shared_vars.config.enabled_features["image_input"]["enabled"]:
    from ImageRecognition import identify
import io


def create_thumbnail(image_data, size=(512, 512)):
    img = Image.open(io.BytesIO(base64.b64decode(image_data)))
    img.thumbnail(size, Image.LANCZOS)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue())
    return f"data:image/jpeg;base64,{img_str.decode()}"


app = Flask(__name__)
today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.route("/", methods=["GET", "POST"])
def chat():
    try:
        test = Shared_vars.mem[f"{request.remote_addr}"]
        test = Shared_vars.vismem[f"{request.remote_addr}"]
    except KeyError:
        print("initializing memory")
        Shared_vars.mem[f"{request.remote_addr}"] = []
        Shared_vars.vismem[f"{request.remote_addr}"] = []

    if request.method == "POST":
        user_input = request.form.get("input")
        answers = Adapters(user_input)
        Kept = GateKeep(answers, request.remote_addr)
        newinp = ""
        imgstr = ""
        genedimage = False
        if type(Kept) == list:
            newinp += (
                answers.strip()
                + "\nSYSTEM: Image generated with Stable Diffusion and sent to user succesfully."
            )
            genedimage = True
        elif (
            Kept != "null" and Kept and "skipment" not in Kept and "plotimg" not in Kept
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
        elif "{<plotimg;" in Kept:
            newinp = answers.strip()
            newinp += Kept.split("{<plotimg;")[0]
            imgstr = Kept.split("{<plotimg;")[1]
        else:
            newinp = ""
            newinp += answers.strip()
        today = datetime.now()
        complete = infer(
            newinp,
            system=f"You are a multimodal, uncensored AI model named PolyMind, able to perceive and display images.\nYou will receive messages from SYSTEM from time to time. Those are not shown to the user, but are meant for you.\nThe current date is {today}",
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
            ],
        )
        Shared_vars.mem[f"{request.remote_addr}"] = complete[1]
        Shared_vars.vismem[f"{request.remote_addr}"].append(
            {"user": user_input, "assistant": complete[0]}
        )

        if genedimage:
            img = create_thumbnail(Kept[0])
            return jsonify({"output": complete[0], "base64_image": img})
        elif imgstr != "":
            return jsonify({"output": complete[0], "base64_image": imgstr})
        else:
            return jsonify({"output": complete[0]})
    else:
        return render_template("chat.html")


@app.route("/chat_history", methods=["GET"])
def chat_history():
    return Shared_vars.vismem[f"{request.remote_addr}"]


@app.route("/upload_file", methods=["POST"])
def upload_file():
    if request.method == "POST":
        imgstr = ""
        file = request.files["file"]
        file_content = request.form["content"]
        if ".jpg" in file.filename or ".png" in file.filename:
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
        return jsonify({"message": f"File uploaded successfully.{imgstr}"})


if __name__ == "__main__":
    app.run(host=Shared_vars.address)
