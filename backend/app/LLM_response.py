
import google.generativeai as genai
genai.configure(api_key="AIzaSyBH6hVJYI6XHlIdmeYcBn4UlPmUWL233aU")
model = genai.GenerativeModel("gemini-2.0-flash")
def get_gemini_answer(best_context, chat_history, query):
    """
    Generate an answer using Gemini model given context, chat history, and query.
    """
    prompt = f"""You are a helpful assistant. Use the following context and conversation to answer the question. Format the answer well.

Context:
{"".join(best_context)}

Conversation:
{chat_history}

Question:
{query}"""

    response = model.generate_content(prompt)
    return response.text
