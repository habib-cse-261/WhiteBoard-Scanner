import os
from dotenv import load_dotenv
load_dotenv()

from google import genai

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"  # Force Developer API mode
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemma-4-31b-it",
    contents="Say hello"
)
print(response.text)