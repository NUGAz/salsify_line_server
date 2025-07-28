import json
import os
from typing import Optional

import aiofiles


class LineIndexer:
    """
    Loads a pre-computed sparse index and serves lines asynchronously by
    reading chunks of the file.
    """

    def __init__(self, filepath: str, cache_path: str):
        self.filepath: str = filepath
        self.cache_path: str = cache_path
        self.offsets: list[int] = []
        self.total_lines: int = 0
        self.index_interval: int = 1
        self.is_ready: bool = False

    async def initialize(self):
        """Asynchronously loads the sparse index from the cache file."""

        print(f"Attempting to load index from cache: '{self.cache_path}'")
        try:
            async with aiofiles.open(self.cache_path, "r") as f:
                content = await f.read()
                cache_data = json.loads(content)
                self.total_lines = cache_data["total_lines"]
                self.offsets = cache_data["offsets"]
                self.index_interval = cache_data["index_interval"]
            self.is_ready = True
            print("Indexer is ready.")
        except FileNotFoundError:
            print(
                f"FATAL: Cache file not found at {self.cache_path}. Server cannot start.",
                file=sys.stderr,
            )
            os._exit(1)

    def line_count(self) -> int:
        return self.total_lines

    async def get_line(self, line_index: int) -> Optional[str]:
        """Asynchronously retrieves a line by reading an entire chunk at once."""
        if not self.is_ready or not 0 <= line_index < self.total_lines:
            return None

        # Determine start and end offsets from the sparse index
        checkpoint_idx = line_index // self.index_interval
        start_offset = self.offsets[checkpoint_idx]
        end_offset = (
            self.offsets[checkpoint_idx + 1]
            if checkpoint_idx + 1 < len(self.offsets)
            else None
        )

        # Read the entire chunk between checkpoints
        chunk = await self._read_chunk(start_offset, end_offset)
        lines_in_chunk = chunk.splitlines()

        # Calculate the line's position within the chunk
        target_line_in_chunk_idx = line_index % self.index_interval

        if target_line_in_chunk_idx < len(lines_in_chunk):
            return lines_in_chunk[target_line_in_chunk_idx].decode("ascii")
        else:
            return None

    async def _read_chunk(self, start_offset: int, end_offset: Optional[int]) -> bytes:
        """Helper method to perform a single async read of a data chunk."""
        read_size = (end_offset - start_offset) if end_offset else -1
        async with aiofiles.open(self.filepath, "rb") as f:
            await f.seek(start_offset)
            return await f.read(read_size)
