"""LC-14  RAG: load -> split -> embed -> store -> retrieve -> answer.  Run: python lc_14_rag_basic.py"""
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from common import get_llm, get_embeddings

# 1) LOAD - normally PDFs/files/DB rows. Here: a tiny fake policy handbook.
raw = [Document(page_content=(
    "Leave policy: Employees get 24 paid leave days per year. Unused leave up to 10 days carries forward. "
    "Work from home: Employees may work from home 2 days per week with manager approval. "
    "Expense policy: Travel expenses above Rs. 5,000 need prior approval from the department head. "
    "Support hours: The IT helpdesk is available Monday to Friday, 9 AM to 6 PM IST."),
    metadata={"source": "handbook.txt"})]

# 2) SPLIT into small chunks (small chunks = precise retrieval)
chunks = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=20).split_documents(raw)
print(f"{len(chunks)} chunks created")

# 3) EMBED + 4) STORE - each chunk becomes a vector; the store searches by similarity
store = InMemoryVectorStore.from_documents(chunks, get_embeddings())

# 5) RETRIEVE - see exactly what comes back for a question
question = "How many days can I work from home?"
for doc, score in store.similarity_search_with_score(question, k=2):
    print(f"  score={score:.3f} | {doc.page_content}")

# 6) ANSWER - stuff retrieved text into the prompt
retriever = store.as_retriever(search_kwargs={"k": 2})
prompt = ChatPromptTemplate.from_template(
    "Answer ONLY from the context. If it is not there, say you don't know.\n\nContext:\n{context}\n\nQuestion: {question}")
format_docs = lambda docs: "\n".join(d.page_content for d in docs)

rag = {"context": retriever | format_docs, "question": lambda x: x} | prompt | get_llm() | StrOutputParser()
print("\nANSWER:", rag.invoke(question))
print("ANSWER:", rag.invoke("What is the CEO's salary?"))      # should say it doesn't know


"""
        STEP 1: LOAD DOCUMENT
        (Company policy handbook)
                   |
                   v
        STEP 2: SPLIT INTO CHUNKS
        Break the handbook into
        small pieces of text
                   |
                   v
        STEP 3: CREATE EMBEDDINGS
        Convert each text piece into
        numbers representing its meaning
                   |
                   v
        STEP 4: STORE IN VECTOR STORE
        Save the chunks so we can
        search them by meaning
                   |
                   v
        =================================
                 USER ASKS
        "How many days can I work
              from home?"
        =================================
                   |
                   v
        STEP 5: RETRIEVE RELEVANT CHUNKS
        Find the most relevant text
        from the handbook
                   |
                   v
        STEP 6: GIVE CONTEXT TO AI
        Send the question + matching
        handbook text to Claude
                   |
                   v
        STEP 7: GENERATE ANSWER
        Claude answers using the
        retrieved information
                   |
                   v
        "Employees may work from home
         2 days per week with
         manager approval."


        WHAT IF THE ANSWER IS MISSING?
        --------------------------------
        Question: "What is the CEO's salary?"
                   |
                   v
        No relevant policy information
                   |
                   v
        Claude: "I don't know."

        
Concept. Instead of hoping the model knows your documents, you look up relevant chunks and paste them into the prompt.

New things in this step

Document and RecursiveCharacterTextSplitter
Embeddings turn text into vectors; InMemoryVectorStore searches by similarity
similarity_search_with_score to inspect retrieval, retriever | format_docs | prompt | llm
Architecture view. THE VECTOR LAYER: index time = chunk, embed, store. Query time = embed the question, fetch top-k chunks, stuff into the prompt. Embeddings run locally.
"""