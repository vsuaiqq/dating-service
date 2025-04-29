import cv2
import numpy as np
from typing import Optional

class VideoValidator:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
    async def analyze_video(self, video_path: str) -> dict:
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {
                    "status": "error",
                    "message": "Could not open video file",
                    "is_human": False
                }
            
            frames_with_face = 0
            total_frames = 0
            face_locations = []
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) > 0:
                    frames_with_face += 1
                    face_locations.extend(faces.tolist())
                total_frames += 1
            
            cap.release()
            
            face_ratio = frames_with_face / total_frames if total_frames > 0 else 0
            is_human = face_ratio > 0.5
            
            return {
                "status": "success",
                "is_human": is_human,
                "face_ratio": face_ratio,
                "total_frames": total_frames,
                "frames_with_face": frames_with_face,
                "face_locations": face_locations
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "is_human": False
            }

    async def validate_video_file(self, file_bytes: bytes) -> dict:
        with NamedTemporaryFile(suffix='.mp4', delete=True) as temp_file:
            temp_file.write(file_bytes)
            temp_file.seek(0)
            return await self.analyze_video(temp_file.name)