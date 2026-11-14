from fastmcp import FastMCP
from pydantic import BaseModel, Field 

mcp = FastMCP("ModernStreamServer")

class DataRequest(BaseModel) :
    user_id: str = Field(..., pattern=r"^USR-\d+$")

@mcp.tool()
def get_user_metrics(request : DataRequest) -> dict :
    """ Fetches high-performance metrics using streamable http """
    return {
        "user" : request.user_id,
        "score" : 98.5,
        "status" : "active",
        "transport_protocol" : "Streamable-HTTP/2.0"
    }

if __name__ == "__main__" :
    mcp.run(
        transport = "streamable-http",
        host = "127.0.0.1",
        port = 8000,
        log_level = "debug"
    )