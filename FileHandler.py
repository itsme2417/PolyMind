from sentence_transformers import SentenceTransformer, util
from Shared_vars import config
import io
from scrape import tokenize, decode
import os
from PyPDF2 import PdfReader
from pathlib import Path
import base64
import hashlib
import numpy as np
import json

model = SentenceTransformer("all-MiniLM-L6-v2")
path = Path(os.path.abspath(__file__)).parent


class NumpyEncoder(json.JSONEncoder):
    """Special json encoder for numpy types"""

    def default(self, obj):
        if isinstance(
            obj,
            (
                np.int_,
                np.intc,
                np.intp,
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
            ),
        ):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def split_into_chunks(text, N):
    tokens = tokenize(text)
    currlen = tokens[0]
    chunks = []

    if currlen <= N:
        return [text]

    for i in range(0, currlen, N):
        chunk = "".join(decode(tokens[1][i : i + N]))
        chunks.append(chunk)

    return chunks


def check_cache(file_name):
    # Construct the full file path
    file_path = os.path.join(path, "embeddings_cache", file_name)

    # Check if the file exists
    if os.path.isfile(file_path):
        # Open and read the file
        with open(file_path, "r") as file:
            return file.read()
    return False


def checkformat(file):
    if "data:application/pdf" in file:
        f = io.BytesIO(base64.b64decode(file.split(";base64,")[1]))
        reader = PdfReader(f)
        text = ""
        for x in reader.pages:
            text += x.extract_text()
        return text
    else:
        return base64.b64decode(file.split(";base64,")[1]).decode("utf-8")
    return file


def queryEmbeddings(query, embeddings, chunks):
    query = model.encode(query)
    simil = []
    # Compute cosine similarity between all pairs
    for i, x in enumerate(embeddings):
        cos_sim = util.cos_sim(query, x)
        simil.append([cos_sim, chunks[i]])

    all_sentence_combinations = sorted(simil, key=lambda x: x[0], reverse=True)
    return all_sentence_combinations[0]


def handleFile(file):
    md5sum = hashlib.md5(file.encode("utf-8")).hexdigest()
    print(f"File hash: {md5sum}")
    file = checkformat(file)
    currlen = tokenize(file)[0]
    print(f"Current length: {currlen}")
    
    if currlen <= config.enabled_features["file_input"]["chunk_size"]:
        return [file]
    else:
        cached = check_cache(f"{md5sum}.json")
        if (
            cached != False
            and json.loads(cached)["chunk_size"]
            == config.enabled_features["file_input"]["chunk_size"]
        ):
            cached = json.loads(cached)
            chunks = cached["chunks"]

            embeddings = cached["embeddings"]
            print("Using cached embeddings.")
        else:
            print("Splitting into chunks")
            chunks = split_into_chunks(
                file, config.enabled_features["file_input"]["chunk_size"]
            )
            print("Creating Embeddings")
            embeddings = model.encode(chunks)
            with open(
                os.path.join(path, "embeddings_cache", f"{md5sum}.json"), "w"
            ) as f:
                json.dump(
                    {
                        "embeddings": embeddings,
                        "chunks": chunks,
                        "chunk_size": config.enabled_features["file_input"][
                            "chunk_size"
                        ],
                    },
                    f,
                    cls=NumpyEncoder,
                )
    return embeddings, chunks
