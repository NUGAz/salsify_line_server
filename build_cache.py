import argparse
import json
import os
import sys
import time

TARGET_INDEX_ENTRIES = 100000
AVG_LINE_LENGTH_BYTES = 80


def _calculate_dynamic_interval(filepath: str) -> int:
    """
    Calculates the sparse index interval based on the file size.
    """

    file_size = os.path.getsize(filepath)
    assert file_size, f"File {filepath} is empty"

    estimated_lines = file_size / AVG_LINE_LENGTH_BYTES
    return max(1, int(estimated_lines // TARGET_INDEX_ENTRIES))


def _perform_indexing_scan(filepath: str, index_interval: int) -> tuple[list[int], int]:
    """
    Scans the file to generate the list of offsets and the total line count.
    Includes a progress indicator for large files.
    """

    offsets = []
    line_count = 0
    current_offset = 0
    total_size = os.path.getsize(filepath)

    with open(filepath, "rb") as f:

        for line in f:
            if line_count % index_interval == 0:
                # The current_offset is the start of the line tha was just read.
                offsets.append(current_offset)

            current_offset += len(line)
            line_count += 1

            if line_count % 10000 == 0 and total_size > 0:
                percent_done = (current_offset / total_size) * 100
                sys.stdout.write(f"Indexing... {percent_done:.1f}% complete\r")
                sys.stdout.flush()

    print()  # Final newline to clear the progress line
    return offsets, line_count


def _save_cache_file(cache_path: str, data: dict):
    """
    Saves the provided data dictionary to a cache file using an atomic write.
    """

    print(f'Saving new index to cache: "{cache_path}"')
    temp_path = cache_path + ".tmp"
    with open(temp_path, "w") as f:
        json.dump(data, f)
    os.rename(temp_path, cache_path)
    print("Cache created successfully.")


def build_sparse_index_and_cache(filepath: str, cache_path: str):
    """
    Build and cache the sparse index.
    """

    print(f'Building sparse in-memory index for "{filepath}"...')
    start_time = time.time()

    index_interval = _calculate_dynamic_interval(filepath)
    print(f"Using dynamic index interval: {index_interval}")

    offsets, total_lines = _perform_indexing_scan(filepath, index_interval)

    print(
        f"Indexing complete. Found {total_lines:,} lines and {len(offsets):,} checkpoints in "
        f"{time.time() - start_time:.2f} seconds."
    )

    cache_data = {
        "total_lines": total_lines,
        "offsets": offsets,
        "index_interval": index_interval,
    }
    _save_cache_file(cache_path, cache_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a sparse index cache for a large text file."
    )
    parser.add_argument(
        "source_file", help="The path to the source text file to index."
    )
    parser.add_argument(
        "cache_file", help="The path where the output index cache file will be saved."
    )
    args = parser.parse_args()

    is_cache_valid = (
        os.path.exists(args.cache_file)
        and os.path.getsize(args.cache_file) > 0
        and os.path.getmtime(args.cache_file) > os.path.getmtime(args.source_file)
    )

    if is_cache_valid:
        print("Cache is already up-to-date.")
    else:
        build_sparse_index_and_cache(args.source_file, args.cache_file)
