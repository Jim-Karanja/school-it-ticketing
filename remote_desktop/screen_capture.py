"""
Screen Capture Service for Remote Desktop
Captures screen and streams it for remote viewing
"""
import cv2
import numpy as np
import threading
import time
import base64
from PIL import ImageGrab
import io
import logging

logger = logging.getLogger(__name__)

class ScreenCapture:
    def __init__(self, quality=70, fps=15):
        self.quality = quality  # JPEG quality (1-100)
        self.fps = fps  # Frames per second
        self.running = False
        self.frame_data = None
        self.clients = set()  # Connected clients
        self.capture_thread = None
        self.frame_lock = threading.Lock()
        
    def start_capture(self):
        """Start screen capture in a separate thread"""
        if self.running:
            return
            
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info(f"Screen capture started at {self.fps} FPS, quality {self.quality}%")
        
    def stop_capture(self):
        """Stop screen capture"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join()
        logger.info("Screen capture stopped")
        
    def _capture_loop(self):
        """Main capture loop"""
        frame_time = 1.0 / self.fps
        
        while self.running:
            start_time = time.time()
            
            try:
                # Capture screen
                screenshot = ImageGrab.grab()
                
                # Convert to numpy array for OpenCV
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Resize for performance (optional)
                height, width = frame.shape[:2]
                if width > 1920:  # Scale down large screens
                    scale = 1920 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Encode as JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                # Convert to base64 for web transmission
                img_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Store frame data
                with self.frame_lock:
                    self.frame_data = {
                        'image': img_base64,
                        'width': frame.shape[1],
                        'height': frame.shape[0],
                        'timestamp': time.time()
                    }
                    
            except Exception as e:
                logger.error(f"Screen capture error: {e}")
                
            # Maintain FPS
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    def get_frame(self):
        """Get the latest frame"""
        with self.frame_lock:
            return self.frame_data.copy() if self.frame_data else None
            
    def add_client(self, client_id):
        """Add a client to receive frames"""
        self.clients.add(client_id)
        if not self.running:
            self.start_capture()
        logger.info(f"Client {client_id} connected to screen capture")
        
    def remove_client(self, client_id):
        """Remove a client"""
        self.clients.discard(client_id)
        if not self.clients and self.running:
            self.stop_capture()
        logger.info(f"Client {client_id} disconnected from screen capture")
        
    def get_stats(self):
        """Get capture statistics"""
        return {
            'running': self.running,
            'clients': len(self.clients),
            'fps': self.fps,
            'quality': self.quality
        }

# Global screen capture instance
screen_capturer = ScreenCapture()
