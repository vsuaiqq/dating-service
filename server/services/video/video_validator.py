import cv2
import face_recognition
from tempfile import NamedTemporaryFile

class VideoValidator:
    def __init__(self, frame_skip: int = 5, face_threshold: float = 0.5):
        self.frame_skip = frame_skip
        self.face_threshold = face_threshold

    def analyze_video_bytes(self, file_bytes: bytes) -> bool:
        with NamedTemporaryFile(suffix=".mp4", delete=True) as temp_file:
            temp_file.write(file_bytes)
            temp_file.flush()
            return self._analyze(temp_file.name)

    def _detect_faces(self, frame) -> list:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return face_recognition.face_locations(rgb)

    def _analyze(self, video_path: str) -> bool:
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False

            frames_with_face = 0
            total_frames = 0
            face_locations = []

            frame_index = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_index % self.frame_skip == 0:
                    faces = self._detect_faces(frame)
                    if faces:
                        frames_with_face += 1
                        face_locations.extend(faces)
                    total_frames += 1

                frame_index += 1

            cap.release()

            if total_frames == 0:
                return False

            face_ratio = frames_with_face / total_frames
            is_human = face_ratio >= self.face_threshold

            return is_human

        except Exception:
            return False
