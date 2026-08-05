from app.llm.model import get_gemini_model

llm = get_gemini_model()

response = llm.invoke("Say hello.")

print(response)