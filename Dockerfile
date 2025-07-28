# Using a lightweight python version is enough for this User Scenario
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
# This leverages Docker's layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY ./line_server ./line_server

# Declare the arguments that will be passed in during the build
ARG APP_PORT
ARG NUM_OF_WORKERS

# Set the arguments as environment variables to make them available at runtime
ENV APP_PORT=$APP_PORT
ENV NUM_OF_WORKERS=$NUM_OF_WORKERS

# Expose the port the app runs on
EXPOSE $APP_PORT

# The command to run the application
# It expects the file path to be passed via the FILE_TO_SERVE environment variable
CMD gunicorn -w $NUM_OF_WORKERS -k uvicorn.workers.UvicornWorker line_server.main:app --bind 0.0.0.0:$APP_PORT
