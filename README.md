# Efficient Line Server

This project is a high-performance, memory-efficient network server designed to serve individual lines from very large text files over a REST API. The system is containerized with Docker and has been optimized to handle high concurrency and massive files with minimal resource usage.

## Features

- **Low Memory Footprint**: Uses a sparse indexing strategy, allowing it to handle multi-gigabyte files with only a few megabytes of RAM.
- **High Concurrency**: Built with FastAPI and Gunicorn, using asynchronous I/O to handle thousands of simultaneous requests.
- **Fast Startup**: A persistent caching mechanism makes server restarts nearly instantaneous after the initial indexing.
- **Portable and Reproducible**: The entire application and its environment are containerized with Docker, ensuring it runs the same everywhere.
- **Robust**: The build and run process is managed by user-friendly shell scripts that handle setup and validation.

---
## Setup and Usage

### Prerequisites

- Docker & Docker Compose
- A Unix-like shell environment (e.g., Linux, macOS, or Git Bash on Windows)

### 1. Configuration

The server's configuration is managed in a single **`.env`** file. This contains the following environment variables:

- `APP_PORT`: The network port the server will listen on.
- `NUM_OF_WORKERS`: The number of Gunicorn worker processes to start. A good default is `(2 * CPU_CORES) + 1`.

### 2. Build the Docker Image

This command reads the `Dockerfile` and builds the application image. It only needs to be run once or after you change the source code or dependencies.

### 3. Run the Server

To run the server, a text file must be provided as argument:

./run.sh <path_to_file.txt>

The first time you run this with a new file, the build_cache.py script will perform a one-time indexing process, which may take several minutes for very large files. Subsequent runs will be instant.

### 4. API Usage

You can request a line using any HTTP client, like curl:

curl http://localhost:8000/lines/<line_index>

or by acessing http://localhost:8000/lines/<line_index> directly

## System Design and Architecture

The system is designed around performance and memory efficiency.

1.  **Pre-computation**: Before the server starts, the `run.sh` script executes `build_cache.py`. This script performs a one-time scan of the source file to create a **sparse index**. Instead of storing the location of every line, it only records the offset of every Nth line (a "checkpoint"). This keeps the index file extremely small, even for massive source files. The result is cached to a `.index` file.
2.  **Server**: The application is a Python server using **FastAPI** for its high speed and async capabilities. It is run by **Gunicorn**, which manages multiple **Uvicorn** worker processes, allowing the application to utilize multiple CPU cores.
3.  **Line Retrieval**: When a request for a line arrives, the server uses the in-memory sparse index to find the nearest checkpoint before the target line. It then performs a single, asynchronous **chunked read** of the data between that checkpoint and the next one. This method is extremely fast and avoids blocking the server, allowing it to handle high concurrency.
4.  **Containerization**: The entire environment is defined in a **`Dockerfile`** and managed by **Docker Compose**. This ensures that the application and its dependencies are consistent and eliminates any "works on my machine" issues.

---
## Performance Analysis

### By File Size (1 GB, 10 GB, 100 GB)

- **Startup Time**: The initial startup requires a full scan of the file to build the cache, a process limited by disk read speed. Subsequent startups are **nearly instantaneous** (under a second) as the server just loads the pre-computed index from the cache.
- **Memory Usage**: Due to the sparse index, the server's RAM usage is **constant and very low** (typically a few megabytes), regardless of the source file's size. It does not load the file or the full index into memory.
- **Request Performance**: Latency is consistently low. The chunked-read approach means that retrieving any line takes roughly the same amount of time, regardless of its position in the file.

### By Concurrent Users (100, 10,000, 1,000,000)

- **100 Users**: The server handles this load with ease.
- **10,000 Users**: A single, powerful machine running this multi-worker setup can handle this load, but system-level tuning (like `ulimit`) is required on the client and server. In a production environment, a load balancer like Nginx would be placed in front.
- **1,000,000 Users**: This scale requires a distributed architecture. The application's stateless design (relying on files) makes it easy to scale horizontally. You would run multiple instances of the container on different machines behind a load balancer, with all instances accessing the data and cache files from a shared network filesystem (like NFS or AWS EFS).

---
## Project Q&A

- **Third-Party Libraries Used?**
    - **FastAPI**: A modern, high-performance web framework for building APIs. Chosen for its speed and native async support.
    - **Gunicorn**: A battle-tested process manager for running production Python web applications. Chosen to manage multiple worker processes.
    - **Uvicorn**: A lightning-fast ASGI server that runs the FastAPI application. Used as the worker class for Gunicorn.
    - **aiofiles**: A library for asynchronous file I/O, essential for preventing the server from blocking on disk reads under heavy load.

- **Documentation Consulted?**
    - Official documentation for Python, Docker, Docker Compose, FastAPI, Gunicorn, Uvicorn, and aiofiles.

- **Future Improvements (Unlimited Time)?**
    - **Distributed Caching**: For a multi-server deployment, replace the file-based cache with a distributed cache like Redis.
    - **Observability**: Add structured logging and export performance metrics to a system like Prometheus for better monitoring.
    - **Formal Python Packaging**: Use a tool like Poetry or Hatch to manage the `pyproject.toml` and lock dependencies, even though it's a containerized service.

- **Critique of the Code?**
    - **Coupling to Filesystem**: The design is tightly coupled to the host filesystem via Docker volumes. While simple, this can be less flexible than other deployment strategies.
    - **Pre-computation Step**: The requirement to run `build_cache.py` before the server can start adds a layer of complexity to the deployment process. A service that is self-contained without a pre-computation step is often simpler to manage.
