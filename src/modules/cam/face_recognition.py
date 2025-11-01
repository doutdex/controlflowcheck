import cv2
import numpy as np
from pathlib import Path
from sklearn.preprocessing import normalize
from typing import Optional, Tuple, List
import urllib.request
import hashlib
import zipfile
import sys
from src.utils.config import config

class FaceRecognition:
    def __init__(self):
        """Initialize face recognition with ResNet model."""
        # Load model paths and thresholds from config
        self.models_dir = getattr(config, 'models_dir', 'models')
        mf = getattr(config, 'model_files', {}) or {}
        self.model_files = {
            "model": mf.get('dnn_model', 'res10_300x300_ssd_iter_140000.caffemodel'),
            "config": mf.get('dnn_config', 'deploy.prototxt')
        }
        self.distance_threshold = float(getattr(config, 'similarity_threshold', 0.6))
        
        # Create models directory (models_dir may be a Path)
        Path(self.models_dir).mkdir(parents=True, exist_ok=True)

        # Download or load models
        self._ensure_models_exist()

        # Load DNN face detector (convert to str for OpenCV)
        model_path = Path(self.models_dir) / self.model_files["model"]
        config_path = Path(self.models_dir) / self.model_files["config"]

        self.face_net = cv2.dnn.readNetFromCaffe(str(config_path), str(model_path))

        # Load face detector cascade as backup
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def _ensure_models_exist(self):
        """Download models if they don't exist."""
        model_url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
        config_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
        
        model_path = Path(self.models_dir) / self.model_files["model"]
        config_path = Path(self.models_dir) / self.model_files["config"]

        if not model_path.exists():
            print("Downloading face detection model...")
            try:
                urllib.request.urlretrieve(model_url, str(model_path))
            except Exception as e:
                print(f"Error downloading model: {e}")
                sys.exit(1)

        if not config_path.exists():
            print("Downloading model configuration...")
            try:
                urllib.request.urlretrieve(config_url, str(config_path))
            except Exception as e:
                print(f"Error downloading config: {e}")
                sys.exit(1)

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces using DNN model with cascade fallback."""
        try:
            # DNN detection
            blob = cv2.dnn.blobFromImage(
                frame, 1.0, (300, 300), 
                [104, 117, 123], False, False
            )
            self.face_net.setInput(blob)
            detections = self.face_net.forward()
            
            faces = []
            h, w = frame.shape[:2]
            
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.5:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    x1, y1, x2, y2 = box.astype(int)
                    faces.append((x1, y1, x2-x1, y2-y1))
            
            return faces
            
        except Exception as e:
            print(f"DNN detection failed, falling back to cascade: {e}")
            # Fallback to cascade detector
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            return [tuple(map(int, face)) for face in faces]

    def get_face_embedding(self, face_img: np.ndarray) -> Optional[np.ndarray]:
        """Extract face features using HOG and LBP."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Resize for consistent features
            face_resized = cv2.resize(gray, (128, 128))
            
            # Calculate HOG features
            win_size = (128, 128)
            block_size = (16, 16)
            block_stride = (8, 8)
            cell_size = (8, 8)
            nbins = 9
            hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, nbins)
            hog_features = hog.compute(face_resized)
            
            # Normalize features
            features = normalize(hog_features.reshape(1, -1))[0]
            return features
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            return None

    def compare_faces(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compare two face embeddings using cosine similarity."""
        try:
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            return float(similarity)
        except Exception as e:
            print(f"Error comparing faces: {e}")
            return 0.0

    def are_same_person(self, embedding1: np.ndarray, embedding2: np.ndarray) -> bool:
        """Determine if two face embeddings belong to the same person."""
        similarity = self.compare_faces(embedding1, embedding2)
        return similarity > self.distance_threshold

    def check_face_quality(self, frame: np.ndarray, face_coords: Tuple[int, int, int, int]) -> Tuple[bool, str]:
        """Check if face meets quality criteria for saving."""
        x, y, w, h = face_coords
        
        # Check minimum face size (60x60 pixels)
        if w < 60 or h < 60:
            return False, "Face too small"
            
        # Check if face is too close to frame borders
        frame_h, frame_w = frame.shape[:2]
        margin = 10
        if x <= margin or y <= margin or x + w >= frame_w - margin or y + h >= frame_h - margin:
            return False, "Face too close to frame borders"
            
        # Check face aspect ratio (width/height should be ~1.0)
        aspect_ratio = w / h
        if not (0.8 <= aspect_ratio <= 1.2):
            return False, "Face not properly aligned"
            
        # Check face orientation using facial landmarks
        try:
            face_roi = frame[y:y+h, x:x+w]
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            
            # Use cascade classifier to detect eyes
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            eyes = eye_cascade.detectMultiScale(gray, 1.1, 3)
            
            if len(eyes) < 2:
                return False, "Eyes not clearly visible"
                
            # Check brightness and contrast
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            if brightness < 40:  # Too dark
                return False, "Image too dark"
            if brightness > 220:  # Too bright
                return False, "Image too bright"
            if contrast < 20:  # Low contrast
                return False, "Low contrast"
                
            return True, "Face quality OK"
            
        except Exception as e:
            print(f"Error checking face quality: {e}")
            return False, "Error analyzing face"

    def process_face(self, frame: np.ndarray, face_coords: Tuple[int, int, int, int]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[str]]:
        """Process detected face and return cropped image with embedding and quality message."""
        try:
            # Check face quality first
            is_quality_ok, quality_message = self.check_face_quality(frame, face_coords)
            if not is_quality_ok:
                return None, None, quality_message
            
            x, y, w, h = face_coords
            pad = 20
            x1 = max(x - pad, 0)
            y1 = max(y - pad, 0)
            x2 = min(x + w + pad, frame.shape[1])
            y2 = min(y + h + pad, frame.shape[0])
            
            face_img = frame[y1:y2, x1:x2]
            face_img = cv2.resize(face_img, (112, 112))
            embedding = self.get_face_embedding(face_img)
            
            return face_img, embedding, quality_message
        except Exception as e:
            print(f"Error processing face: {e}")
            return None, None, "Error processing face"
