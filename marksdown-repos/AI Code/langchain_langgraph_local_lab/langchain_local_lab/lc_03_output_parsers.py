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


"""
Concept. A parser converts the model's output into something your code can use. The | pipe connects steps into a chain.

New things in this step

prompt | llm | parser
StrOutputParser (AIMessage to str)
JsonOutputParser (text to dict, tolerates ```json fences)
Architecture view. Chain = three steps run left to right; the output of each is the input of the next.

"""