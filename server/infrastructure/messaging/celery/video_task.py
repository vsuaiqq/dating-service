from infrastructure.messaging.celery.base_task import KafkaTask
from services.video.video_validator import VideoValidator

class VideoValidationTask(KafkaTask):
    abstract = True

    _validator: VideoValidator = None

    @property
    def video_validator(self) -> VideoValidator:
        if self._validator is None:
            self._validator = VideoValidator(frame_skip=5, face_threshold=0.5)
        return self._validator
