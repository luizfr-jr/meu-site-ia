import os
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
print("🔑 OPENROUTER_API_KEY:", api_key)

headers = {
    "Authorization": f"Bearer {api_key}",
    "HTTP-Referer": "http://localhost",  # Pode colocar seu domínio real se tiver
    "User-Agent": "kallebyevangelho03@gmail.com"  # Pode usar seu e-mail
}

data = {
    "model": "mistralai/mistral-7b-instruct",
    "messages": [
        {"role": "user", "content": "Olá, quem é você?"}
    ]
}

response = httpx.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)

if response.status_code == 200:
    resposta = response.json()
    print("\n✅ Resposta:\n", resposta["choices"][0]["message"]["content"])
else:
    print("❌ Erro:", response.status_code, response.text)