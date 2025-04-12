FROM ubuntu:22.04

# Set noninteractive mode for package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the MediaMTX executable and config
COPY mediamtx/ /app/mediamtx/

# Copy the video file
COPY input.mp4 /app/

# Copy the Python script
COPY stream.py /app/

# Make sure the MediaMTX binary is executable
RUN chmod +x /app/mediamtx/mediamtx

# Expose the RTSP port
EXPOSE 8554

# Start the streaming application
CMD ["python3", "stream.py"]
