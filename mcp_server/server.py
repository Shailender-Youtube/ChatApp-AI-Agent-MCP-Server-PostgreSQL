# mcp_server/server.py
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import uvicorn

load_dotenv()  # loads PG_HOST, PG_USER, PG_PASS, PG_DB

app = FastAPI()

def query_postgres_tool(query: str):
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASS"),
        dbname=os.getenv("PG_DB")
    )
    with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()

@app.post("/query_postgres")
async def query_postgres_endpoint(request: Request):
    """
    Expects JSON of the form {"query": "..."}.
    Returns {"rows": [...]} with all non‑JSON types converted.
    """
    body = await request.json()
    sql = body.get("query")
    if not sql:
        return JSONResponse(status_code=400, content={"error": "Missing 'query' in request body."})

    try:
        rows = query_postgres_tool(sql)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    # Use jsonable_encoder to handle dates, decimals, etc.
    payload = {"rows": rows}
    return JSONResponse(content=jsonable_encoder(payload))

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
