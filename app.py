from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain.callbacks import AsyncIteratorCallbackHandler
from typing import AsyncIterable, Awaitable
from fastapi.responses import StreamingResponse
import openai
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

messages = []
subject = "wine"
instructor = f"""You're a assistant helping humans. Please answer questions as detail as possible.
                And please format them in a user-friendly way, easy to read.
                If human's asking about something that is not related with ${subject}, just tell him you only answer about ${subject}.
            """
remember_cnt = 10


def initializeMemory():
    global messages
    messages = []


initializeMemory()


class Message(BaseModel):
    message: str


async def send_message(message: str) -> AsyncIterable[str]:

    messages.append({'role': 'user', 'content': message})
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[{'role': 'system', 'content': instructor}] +
        messages[-remember_cnt:],
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

    messages.append({'role': 'assistant', 'content': final})


@app.post("/memory-clear")
async def memory_clear():
    initializeMemory()


@app.post("/chat")
async def get_answer(message: Message):
    return StreamingResponse(send_message(message.message), media_type='text/event-stream')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(host="0.0.0.0", port=8080, app=app)
