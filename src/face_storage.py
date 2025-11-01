import logging
import cv2
import base64
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import os
from face_recognition import FaceRecognition
from utils.config import config

class FaceStorage:
    def __init__(self):
        self.faces: List[Dict] = []

        # Load values from config (config.detected_faces_dir is a Path)
        self.save_dir: Path = Path(config.detected_faces_dir)
        self.last_detection_time = datetime.now()
        # Minimum time between attempts to save (avoid extremely rapid saves)
        self.min_detection_interval = timedelta(seconds=float(config.min_detection_interval_seconds))
        # Don't save repeats within this many seconds for the same face
        self.repeat_interval_seconds = float(config.repeat_interval_seconds)
        # Track last saved face (embedding + timestamp) to quickly detect repeats
        self.last_saved: Optional[Dict] = None
        self.face_recognizer = FaceRecognition()

        # ensure save dir exists
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.setup_logging()

    def setup_logging(self):
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'face_storage.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def find_similar_face(self, new_embedding: np.ndarray, recent_seconds: int = None) -> Optional[Dict]:
        """Return a stored face dict that is similar to new_embedding (within recent_seconds), or None."""
        if not self.faces or new_embedding is None:
            return None
        if recent_seconds is None:
            recent_seconds = float(config.recent_seconds)

        recent_time = datetime.now() - timedelta(seconds=float(recent_seconds))
        recent_faces = [f for f in self.faces if f["timestamp"] > recent_time]

        for stored_face in recent_faces:
            if "embedding" in stored_face:
                try:
                    if self.face_recognizer.are_same_person(
                        new_embedding,
                        np.array(stored_face["embedding"])
                    ):
                        return stored_face
                except Exception as e:
                    self.logger.debug(f"Error comparing embeddings: {e}")
        return None

    def save_face(self, frame: np.ndarray, face_coords: Tuple[int, int, int, int]) -> bool:
        """Save face if quality ok and not duplicate within repeat interval."""
        current_time = datetime.now()
        if current_time - self.last_detection_time < self.min_detection_interval:
            return False

        face_img, embedding, quality_message = self.face_recognizer.process_face(frame, face_coords)

        if face_img is None or embedding is None:
            self.logger.warning(f"Face rejected: {quality_message}")
            return False

        # Quick check against last saved face to avoid immediate repeats
        if self.last_saved and "embedding" in self.last_saved:
            try:
                last_emb = np.array(self.last_saved["embedding"])
                if self.face_recognizer.are_same_person(embedding, last_emb):
                    elapsed_last = (current_time - self.last_saved["timestamp"]).total_seconds()
                    if elapsed_last < self.repeat_interval_seconds:
                        self.logger.info(f"Similar to last saved (elapsed {int(elapsed_last)}s) — skipping save")
                        return False
                    else:
                        self.logger.info(f"Similar to last saved but older ({int(elapsed_last)}s) — will save")
            except Exception as e:
                self.logger.debug(f"Error comparing with last_saved: {e}")

        # Fallback: check other recent stored faces (older records)
        similar = self.find_similar_face(embedding, recent_seconds=float(config.recent_seconds))
        if similar is not None:
            elapsed = (current_time - similar["timestamp"]).total_seconds()
            if elapsed < self.repeat_interval_seconds:
                self.logger.info(f"Similar face detected (elapsed {int(elapsed)}s) — skipping save")
                return False
            self.logger.info(f"Similar face found but older ({int(elapsed)}s) — saving new record")

        # encode + save
        ok, buf = cv2.imencode(".jpg", face_img)
        if not ok:
            self.logger.error("Failed to encode face image")
            return False

        b64_img = base64.b64encode(buf).decode("utf-8")
        timestamp_str = current_time.strftime('%Y%m%d_%H%M%S')
        filepath = self.save_dir / f"face_{timestamp_str}.jpg"
        filename = str(filepath)
        try:
            cv2.imwrite(filename, face_img)
        except Exception as e:
            self.logger.error(f"Failed to write face image to disk: {e}")
            filename = None

        face_data = {
            "timestamp": current_time,
            "image": b64_img,
            "embedding": embedding.tolist(),
            "quality": quality_message,
            "filename": filename
        }
        self.faces.append(face_data)
        self.last_detection_time = current_time
        # update last_saved reference
        try:
            self.last_saved = {"timestamp": current_time, "embedding": embedding.tolist(), "filename": filename}
        except Exception:
            self.last_saved = None

        self.logger.info(f"New face saved at {current_time.strftime('%Y-%m-%d %H:%M:%S')} - Quality: {quality_message} - file: {filename}")
        return True