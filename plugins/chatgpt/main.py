from openai import OpenAI

client = OpenAI(api_key="")


def main(params, memory, infer, ip, Shared_vars):

    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": params['message']}
    ],
    max_tokens=250
    )
    return f"Here is the response from chatgpt as requested by the user, remember that you are not talking to chatgpt, but the USER, and the user also cannot see this message.\nCHATGPT RESPONSE: {completion.choices[0].message.content}"
if __name__ == "__main__":
    main(params, memory, infer, ip, Shared_vars)