import os
import sys
from line_server.line_indexer import LineIndexer
from fastapi import FastAPI, Response, status
from fastapi.responses import PlainTextResponse

# Environment Setup
FILE_PATH = os.environ.get("FILE_TO_SERVE")
CACHE_PATH = os.environ.get("CACHE_FILE_PATH")

assert FILE_PATH or os.path.exists(FILE_PATH), \
        f'FATAL ERROR: File not found at given path {FILE_PATH}.'

assert CACHE_PATH, \
        f'FATAL ERROR: File not found at given path {CACHE_PATH}.'

# FastAPI Setup 
# Create the indexer instance, but don't initialize it yet.
indexer = LineIndexer(FILE_PATH, CACHE_PATH)

app = FastAPI(
    title="Line Server",
    description="A REST server to serve lines from a text file efficiently.",
)

# Use a startup event to run the async initialization.
@app.on_event("startup")
async def startup_event():
    """Initializes line indexer when the application starts."""
    await indexer.initialize()


@app.get(
    "/lines/{line_index}",
    response_class=PlainTextResponse,
    responses={
        200: {"description": "The requested line text.", "content": {"text/plain": {}}},
        413: {"description": "Line index is out of the file's bounds."},
    },
)

async def serve_line(line_index: int, response: Response):
    """API endpoint."""

    line = await indexer.get_line(line_index)
    if line is None:
        response.status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        return f"Error: Line index {line_index} is out of bounds. File has {indexer.line_count()} lines (0-indexed)."
    return line

@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Welcome to the Line Server!",
        "file_being_served": FILE_PATH,
        "total_lines": indexer.line_count(),
        "api_docs": "/docs",
    }
