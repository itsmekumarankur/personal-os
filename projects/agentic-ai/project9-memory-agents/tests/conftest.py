import os
import tempfile

# main.py creates its MemoryStore when it is imported, so point it at a temp folder first.
os.environ.setdefault("MEMORY_DIR", tempfile.mkdtemp(prefix="memory-tests-"))
