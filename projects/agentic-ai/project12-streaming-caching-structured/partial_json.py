"""Best-effort reading of JSON that is still being typed.

While a tool call streams you get fragments like  {"vendor": "Acme Tra   . You can show the user progress if you can read the part that exists.
Method: remember what is open (string / object / array), then close it. Anything half-typed at the end is dropped, because
'3' might still become '3.5' and 'tru' is not yet a boolean. The result is ALWAYS a hint for the screen, NEVER a value to act on:
act only after content_block_stop, when json.loads of the whole string works.
"""
import json


def parse_partial(s: str):
    """Returns the parsed prefix, or None if nothing useful yet."""
    stack, in_str, esc = [], False, False
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()
    candidate = s
    if in_str:
        candidate += '"'
    # try closing; if the tail is a dangling key/colon/comma/number fragment, trim it back until it parses
    closers = "".join("}" if c == "{" else "]" for c in reversed(stack))
    for cut in range(len(candidate), 0, -1):
        attempt = candidate[:cut]
        attempt = attempt.rstrip().rstrip(",")
        for tail in ("", "null"):
            try:
                return json.loads(attempt + tail + closers)
            except ValueError:
                continue
        # recompute closers for the shorter text
        st, ins, es = [], False, False
        for ch in candidate[:cut]:
            if ins:
                es = (not es) if ch == "\\" else False
                if ch == '"' and not es:
                    ins = False
                continue
            if ch == '"':
                ins = True
            elif ch in "{[":
                st.append(ch)
            elif ch in "}]" and st:
                st.pop()
        closers = ("\"" if ins else "") + "".join("}" if c == "{" else "]" for c in reversed(st))
    return None
