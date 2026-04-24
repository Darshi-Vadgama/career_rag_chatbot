# app/services/llm_service.py
# FINAL MISTRAL CLOUD LLM SERVICE

import os
from langchain_mistralai import ChatMistralAI

llm = ChatMistralAI(
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral-small-latest",   # fast + good
    temperature=0.3,
    max_tokens=800
)                   

async def ask_llm(prompt:str):
    res = llm.invoke(prompt)
    return res.content