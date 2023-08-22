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
instructor = f"""You're a professional beverages consultant speaking Lithuanian and helping humans. Please answer questions as detailed as possible.
                Before recommending anything make sure a person is healthy and at least 20 years old. Person has to answer yes and only then proceed with recommendations.
                And please format them in a user-friendly way, easy to read.
                If a human asks about something unrelated to {subject}, tell him you only answer about {subject}.
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
        model='gpt-3.5-turbo',
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
