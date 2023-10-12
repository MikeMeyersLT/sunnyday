from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain.callbacks import AsyncIteratorCallbackHandler
from typing import AsyncIterable, Awaitable
from fastapi.responses import StreamingResponse
import openai
import os
from typing import List
import uuid

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

subject = "wine, alcoholic and non-alcoholic beverages"
instructor = f"""You're a professional, smart beverages consultant and helping humans. Please answer questions as detailed as possible.
And please format them in a user-friendly way, easy to read.
You must answer in Lithuanian based on below rules.



```````
- Before answer for anything make sure a person is healthy and at least 20 years old. Person has to answer yes and only then proceed with recommendations.
If person answers no, then do not recommend anything and do not answer any questions. Do not answer any questions until you know the person's age, but only ask if the person is at least 20 years old.
- Under the condition of a healthy person over 20 years of age, If a human asks about discounts or anything related to that answer that any discounts are not allowed anything related alcoholic beverages. Discounts related to beverages does not exist anywhere. Do not answer if a human asks where he can find discounts. anything related to discounts about any subject should not be answered.
- Do not answer questions that are similar to: does wine or other drinks help me relax? Will I feel better drinking? Alcoholic drinks influence shouldn't be discussed at all.
- If a human has questions about something unrelated to {subject}, tell him you only answer about {subject}. you must not answer for that question.
```````



You must speak in Lithuanian.
            """
remember_cnt = 10


class Message(BaseModel):
    role: str
    content: str


class MessageList(BaseModel):
    message: list[Message]


def send_message(message: MessageList) -> AsyncIterable[str]:
    msg = [{'role': 'system', 'content': instructor}]
    for m in message.message:
        msg.append(m.dict())
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=msg,
        temperature=0,
        stream=True
    )

    final = ""
    for chunk in response:
        if 'content' in chunk.choices[0].delta:
            string = chunk.choices[0].delta.content
            final += string
            if string.isspace() and len(string.strip()) == 0:
                yield '\n'
            else:
                yield string


@app.post("/chat")
async def get_answer(message: MessageList):
    print("asdf")
    return StreamingResponse(send_message(message), media_type='text/event-stream')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(host="0.0.0.0", port=8080, app=app)
