import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    """Handles deep image analysis: EXIF metadata and InsightFace facial recognition."""
    
    def __init__(self):
        self.face_app = None
        self.cv2 = None
        self.np = None
        
    def _init_insightface(self):
        if self.face_app is not None:
            return
        try:
            import cv2
            import numpy as np
            from insightface.app import FaceAnalysis
            
            # Initialize with lightweight model for memory efficiency
            self.face_app = FaceAnalysis(name='buffalo_sc', providers=['CPUExecutionProvider'])
            self.face_app.prepare(ctx_id=0, det_size=(640, 640))
            self.cv2 = cv2
            self.np = np
            logger.info("InsightFace (buffalo_sc) initialized successfully.")
        except ImportError:
            logger.warning("InsightFace or OpenCV not installed. Facial recognition will be skipped. Run 'pip install insightface opencv-python onnxruntime'")
            self.face_app = False
        except Exception as e:
            logger.error(f"Error initializing InsightFace: {e}")
            self.face_app = False

    def analyze(self, image_path: str) -> dict:
        from osint.extractors.exif_extractor import ExifExtractor
        
        results = {
            "exif": {},
            "faces": [],
            "image_path": image_path
        }
        
        # 1. EXIF Extraction
        results["exif"] = ExifExtractor.extract(image_path)
        
        # 2. Face Recognition
        self._init_insightface()
        if self.face_app and self.face_app is not False and os.path.exists(image_path):
            try:
                img = self.cv2.imread(image_path)
                if img is not None:
                    faces = self.face_app.get(img)
                    for i, face in enumerate(faces):
                        # Convert embedding array to list for JSON serialization
                        embedding = face.embedding.tolist() if hasattr(face, 'embedding') else []
                        results["faces"].append({
                            "face_id": f"face_{i}",
                            "age": int(face.age) if hasattr(face, 'age') else None,
                            "gender": "male" if hasattr(face, 'gender') and face.gender == 1 else "female",
                            "bbox": face.bbox.tolist() if hasattr(face, 'bbox') else [],
                            "embedding": embedding
                        })
            except Exception as e:
                logger.error(f"Face analysis failed: {e}")
                
        return results
        
    def compare_faces(self, embedding1: list, embedding2: list, threshold=0.6) -> bool:
        """Compare two face embeddings using cosine similarity."""
        self._init_insightface()
        if not self.face_app or self.face_app is False or not embedding1 or not embedding2:
            return False
        try:
            e1 = self.np.array(embedding1)
            e2 = self.np.array(embedding2)
            similarity = self.np.dot(e1, e2) / (self.np.linalg.norm(e1) * self.np.linalg.norm(e2))
            return similarity > threshold
        except Exception:
            return False
