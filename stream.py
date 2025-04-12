#!/usr/bin/env python3

import subprocess
import time
import os
import signal
import sys
import socket

def check_port_open(host, port):
    """Check if a port is open on a host"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def main():
    # Define paths and settings
    mediamtx_path = "/app/mediamtx/mediamtx"
    mediamtx_config = "/app/mediamtx/mediamtx.yml"
    input_video = "/app/input.mp4"
    rtsp_url = "rtsp://127.0.0.1:8554/live/stream"
    rtsp_port = 8554

    # Verify files exist
    if not os.path.exists(mediamtx_path):
        print(f"ERROR: MediaMTX binary not found at {mediamtx_path}")
        sys.exit(1)
    if not os.path.exists(mediamtx_config):
        print(f"ERROR: MediaMTX config not found at {mediamtx_config}")
        sys.exit(1)
    if not os.path.exists(input_video):
        print(f"ERROR: Input video not found at {input_video}")
        sys.exit(1)
        
    print(f"Working directory: {os.getcwd()}")
    print("Files in current directory:")
    for f in os.listdir():
        print(f"  - {f}")
        
    print("Files in MediaMTX directory:")
    for f in os.listdir("mediamtx"):
        print(f"  - {f}")
    
    # Start MediaMTX server
    print("Starting MediaMTX RTSP server...")
    mediamtx_process = subprocess.Popen(
        [mediamtx_path, mediamtx_config],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Check if process started
    if mediamtx_process.poll() is not None:
        print("ERROR: MediaMTX failed to start")
        stdout, stderr = mediamtx_process.communicate()
        print(f"STDOUT: {stdout.decode('utf-8')}")
        print(f"STDERR: {stderr.decode('utf-8')}")
        sys.exit(1)
    
    # Wait for MediaMTX to start and the RTSP port to be ready
    print(f"Waiting for RTSP server to be ready on port {rtsp_port}...")
    max_retries = 20
    retries = 0
    
    while not check_port_open("127.0.0.1", rtsp_port):
        time.sleep(1)
        retries += 1
        print(f"RTSP not ready yet, waiting... (attempt {retries}/{max_retries})")
        
        # Check if MediaMTX is still running
        if mediamtx_process.poll() is not None:
            print("ERROR: MediaMTX stopped unexpectedly")
            stdout, stderr = mediamtx_process.communicate()
            print(f"STDOUT: {stdout.decode('utf-8')}")
            print(f"STDERR: {stderr.decode('utf-8')}")
            sys.exit(1)
        
        if retries >= max_retries:
            print("Failed to start RTSP server within the timeout period")
            mediamtx_process.terminate()
            sys.exit(1)
    
    print("RTSP server is ready!")
    
    # Start FFmpeg to loop the video and push it to the RTSP server
    print("Starting FFmpeg to stream video...")
    ffmpeg_cmd = [
        "ffmpeg",
        "-re",               # Read input at native frame rate
        "-stream_loop", "-1", # Loop the input indefinitely
        "-i", input_video,   # Input file
        "-c", "copy",        # Copy codec without re-encoding
        "-f", "rtsp",        # Output format RTSP
        "-rtsp_transport", "tcp", # Use TCP for RTSP
        rtsp_url             # RTSP URL
    ]
    
    ffmpeg_process = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Check if FFmpeg started
    if ffmpeg_process.poll() is not None:
        print("ERROR: FFmpeg failed to start")
        stdout, stderr = ffmpeg_process.communicate()
        print(f"STDOUT: {stdout.decode('utf-8')}")
        print(f"STDERR: {stderr.decode('utf-8')}")
        mediamtx_process.terminate()
        sys.exit(1)
    
    print(f"✅ RTSP stream is now available at {rtsp_url}")
    print(f"✅ Access from host at rtsp://<host-ip>:8555/live/stream")
    
    # Keep the main process running
    try:
        while True:
            # Check if processes are still running
            if mediamtx_process.poll() is not None:
                print("WARNING: MediaMTX process stopped unexpectedly")
                stdout, stderr = mediamtx_process.communicate()
                print(f"STDOUT: {stdout.decode('utf-8')}")
                print(f"STDERR: {stderr.decode('utf-8')}")
                break
            
            if ffmpeg_process.poll() is not None:
                print("WARNING: FFmpeg process stopped unexpectedly")
                stdout, stderr = ffmpeg_process.communicate()
                print(f"STDOUT: {stdout.decode('utf-8')}")
                print(f"STDERR: {stderr.decode('utf-8')}")
                break
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        # Clean up
        print("Stopping processes...")
        if mediamtx_process.poll() is None:
            mediamtx_process.terminate()
            print("MediaMTX stopped")
        if ffmpeg_process.poll() is None:
            ffmpeg_process.terminate()
            print("FFmpeg stopped")
        
    print("Stream stopped")

if __name__ == "__main__":
    main()
