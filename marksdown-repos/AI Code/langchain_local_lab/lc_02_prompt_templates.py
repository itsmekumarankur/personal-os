"""LC-02  Prompt templates = reusable messages with {variables}.  Run: python lc_02_prompt_templates.py"""
from langchain_core.prompts import ChatPromptTemplate
from common import get_llm

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}. Answer in {style}."),
    ("human", "{question}"),
])
print("variables the template needs:", prompt.input_variables)

# A template is a Runnable: .invoke() fills the blanks. NO model is called yet.
filled = prompt.invoke({"role": "bank teller", "style": "two short sentences", "question": "What is a demat account?"})
print("\nfilled prompt (what the model will receive):")
for m in filled.to_messages():
    print(f"  [{m.type}] {m.content}")

# Only now do we send it to the model.
print("\nmodel answer:", get_llm().invoke(filled).text)

"""
    Concept. A template is a reusable message with {blanks}. Filling it is a separate step from calling the model.
    
    New things in this step
    - ChatPromptTemplate.from_messages
    - prompt.input_variables
    - A template is a Runnable too: .invoke(dict) returns the filled messages
    Architecture view. Template (pure Python string formatting) -> filled messages -> model. 
                       No model is involved until the last line.

"""