#!/bin/bash

# Stop previous processes
pkill -f mediamtx
pkill -f ffmpeg

# Start MediaMTX
echo "Starting MediaMTX..."
./mediamtx/mediamtx ./mediamtx/mediamtx.yml &
MEDIAMTX_PID=$!
echo "MediaMTX started with PID $MEDIAMTX_PID."

# Wait for MediaMTX RTSP port to be open (RTSP listening on 8554)
echo "Waiting for RTSP service to be ready..."
until nc -z localhost 8554; do
    echo "RTSP not ready yet, waiting..."
    sleep 1
done
echo "RTSP port is ready!"

# Start FFmpeg and push stream via RTSP
echo "Starting FFmpeg..."
ffmpeg -re -stream_loop -1 -i input.mp4 -c copy -rtsp_transport tcp -f rtsp rtsp://localhost:8554/live/stream &
FFMPEG_PID=$!
echo "FFmpeg started with PID $FFMPEG_PID."

echo "✅ RTSP stream is now available at rtsp://localhost:8554/live/stream."

