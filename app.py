from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel
from langchain.callbacks import AsyncIteratorCallbackHandler
from typing import AsyncIterable, Awaitable
from fastapi.responses import StreamingResponse
import asyncio

load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

memory = ConversationSummaryBufferMemory(llm=OpenAI())


class Message(BaseModel):
    message: str


async def send_message(message: str) -> AsyncIterable[str]:

    callback = AsyncIteratorCallbackHandler()

    conversation_chain = ConversationChain(
        llm=ChatOpenAI(streaming=True, callbacks=[
                       callback], model="gpt-3.5-turbo", max_tokens=8000),
        memory=memory,
    )

    async def wrap_done(fn: Awaitable, event: asyncio.Event):
        try:
            await fn
        except Exception as e:
            print(f"Caught exception: {e}")
        finally:
            event.set()

    task = asyncio.create_task(wrap_done(
        conversation_chain.apredict(input=message),
        callback.done
    ))

    data = ""
    async for token in callback.aiter():
        data += token
        print(repr(f"data:{token}"))
        yield f"{token}"

    await task


@app.post("/memory-clear")
async def memory_clear():
    memory.clear()


@app.post("/chat")
async def get_answer(message: Message):
    return StreamingResponse(send_message(message.message), media_type='text/event-stream')

if name == "main":
    import uvicorn
    uvicorn.run(host="0.0.0.0", port=8080, app=app)
