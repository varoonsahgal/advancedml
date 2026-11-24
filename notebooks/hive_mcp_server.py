"""A tiny MCP server exposing the hive tools over stdio."""
import ast, json, math, operator, os
try:
    from mcp.server.mcpserver import MCPServer           # mcp >= 2
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer  # mcp 1.x
from sklearn.feature_extraction.text import TfidfVectorizer

server = MCPServer("hive-tools")

CORPUS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hive_corpus.json")))
_VEC = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
_X = _VEC.fit_transform([d["text"] for d in CORPUS])

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg}
_FUNCS = {"sqrt": math.sqrt, "log": math.log, "exp": math.exp, "abs": abs}

def _ev(n):
    if isinstance(n, ast.Expression): return _ev(n.body)
    if isinstance(n, ast.Constant) and type(n.value) in (int, float): return n.value
    if isinstance(n, ast.BinOp) and type(n.op) in _OPS: return _OPS[type(n.op)](_ev(n.left), _ev(n.right))
    if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS: return _OPS[type(n.op)](_ev(n.operand))
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FUNCS:
        return _FUNCS[n.func.id](*[_ev(a) for a in n.args])
    raise ValueError(f"disallowed: {type(n).__name__}")

@server.tool()
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression exactly (+ - * / // % ** sqrt log exp abs)."""
    return str(_ev(ast.parse(expression.replace("^", "**"), mode="eval")))

@server.tool()
def retrieve_docs(query: str, k: int = 3) -> str:
    """Search the course glossary; returns the top-k passages prefixed with [doc_id]."""
    scores = (_X @ _VEC.transform([query]).T).toarray().ravel()
    top = scores.argsort()[::-1][:k]
    return "\n".join(f"[{CORPUS[i]['id']}] {CORPUS[i]['text']}" for i in top)

if __name__ == "__main__":
    server.run()   # stdio transport by default
