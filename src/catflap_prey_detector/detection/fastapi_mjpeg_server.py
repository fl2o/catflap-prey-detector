import io
import logging
from contextlib import asynccontextmanager
from pprint import pprint
from threading import Condition
from typing import AsyncGenerator, Generator
import cv2
import time

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from picamera2 import Picamera2, MappedArray
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput
from libcamera import controls, Transform

from catflap_prey_detector.detection.config import camera_config


# Configuration
display_stream = "main" 
display_size = (640, 360) # 640*9/16
main_size = (640, 360) # 640*9/16

# for full view, ref = 4608 x 2592 = 16 / 9 with mode 1 or 2

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Picamera2 MJPEG Streaming (FastAPI)</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #f0f0f0;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        img {
            border: 2px solid #ddd;
            border-radius: 5px;
            max-width: 100%;
            height: auto;
        }
        .info {
            margin-top: 20px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Hello 👋</h1>
        <img src="/stream.mjpg" alt="Camera Stream" />
    </div>
</body>
</html>
"""

def apply_timestamp(request):
    colour = (0, 255, 0)
    origin = (0, 30)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1
    thickness = 2
    timestamp = time.strftime("%Y-%m-%d %X")
    with MappedArray(request, display_stream) as m:
        cv2.putText(m.array, timestamp, origin, font, scale, colour, thickness)

class StreamingOutput(io.BufferedIOBase):
    """Thread-safe buffer for MJPEG frames"""
    
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf: bytes) -> int:
        """Write a new frame and notify waiting consumers"""
        with self.condition:
            self.frame = buf
            self.condition.notify_all()
        return len(buf)


output = StreamingOutput()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events"""
    try:
        picam2 = Picamera2()
        picam2.pre_callback = apply_timestamp

        modes = picam2.sensor_modes
        mode = modes[1]
        
        config = picam2.create_video_configuration(
            sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']},
            transform=Transform(vflip=camera_config.vflip, hflip=camera_config.hflip),
            main={'size': main_size},
            lores={'size': display_size},
        )
        
        # picam2.align_configuration(config)

        picam2.configure(config)
        pprint(picam2.camera_configuration())
        picam2.start_recording(MJPEGEncoder(), FileOutput(output), name=display_stream)
        picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        logging.info(f"Camera recording started - Streaming at {display_size} resolution")
    except Exception as e:
        logging.error(f"Failed to start camera: {e}")
        raise
    
    yield
    
    try:
        picam2.stop_recording()
        logging.info("Camera recording stopped")
    except Exception as e:
        logging.error(f"Error stopping camera: {e}")


app = FastAPI(
    title="Picamera2 MJPEG Server",
    description="MJPEG streaming server for Picamera2 using FastAPI",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main camera viewing page"""
    return HTML_PAGE

def generate_frames() -> Generator[bytes, None, None]:
    """Generator function that yields MJPEG frames"""
    while True:
        try:
            with output.condition:
                output.condition.wait() 
                if output.frame is None:
                    continue
                frame = output.frame
            
            yield (b'--FRAME\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame)).encode() + b'\r\n'
                   b'\r\n' + frame + b'\r\n')
                   
        except Exception as e:
            logging.warning(f"Error generating frame: {e}")
            break


@app.get("/stream.mjpg")
async def video_stream():
    """MJPEG video stream endpoint"""
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=FRAME"
    )


if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    uvicorn.run(
        "fastapi_mjpeg_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  
        log_level="info"
    )
