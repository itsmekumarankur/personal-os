"""LC-03  Output parsers + your first chain using the | pipe.  Run: python lc_03_output_parsers.py"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from common import get_llm

llm = get_llm()

# Parser 1: AIMessage -> plain str. The | operator means "feed output of left into right".
str_chain = ChatPromptTemplate.from_template("Name one famous {thing}. Reply with the name only.") | llm | StrOutputParser()
result = str_chain.invoke({"thing": "Indian river"})
print("str parser  -> is a str:", isinstance(result, str), "|", result)

# Parser 2: model text -> Python dict.
json_chain = (
    ChatPromptTemplate.from_template(
        "Give details about the city {city} as JSON with keys: country, population_millions, famous_for. "
        "Return ONLY JSON."
    )
    | llm
    | JsonOutputParser()
)
data = json_chain.invoke({"city": "Chennai"})
print("json parser ->", type(data).__name__, "|", data)
print("famous_for  =", data.get("famous_for"))
