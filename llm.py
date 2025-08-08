import os
from openai import OpenAI

def call_openai(system_prompt: str, user_data: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

    completion = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_data}
        ]
    )
    return completion.choices[0].message.content