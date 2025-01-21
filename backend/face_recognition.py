import numpy as np
import base64
import cv2
from typing import Dict, Optional
import pickle
import os
from pathlib import Path
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import torchvision.transforms as transforms

class FaceRecognitionSystem:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.mtcnn = MTCNN(
            image_size=160, margin=0, min_face_size=20,
            thresholds=[0.6, 0.7, 0.7], factor=0.709, post_process=True,
            device=self.device
        )
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        self.known_faces = {}
        self.data_dir = Path("data/faces")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.face_data_file = self.data_dir / "known_faces.pkl"
        self.load_known_faces()

    def load_known_faces(self) -> None:
        try:
            if self.face_data_file.exists():
                with open(self.face_data_file, 'rb') as f:
                    self.known_faces = pickle.load(f)
                print(f"Loaded {len(self.known_faces)} face(s) from storage")
        except Exception as e:
            print(f"Error loading face data: {e}")
            self.known_faces = {}

    def save_known_faces(self) -> None:
        try:
            with open(self.face_data_file, 'wb') as f:
                pickle.dump(self.known_faces, f)
            print("Face data saved successfully")
        except Exception as e:
            print(f"Error saving face data: {e}")

    def extract_face(self, image_data: str, required_size=(160, 160)) -> Dict:
        try:
            image = self._base64_to_image(image_data)
            if image is None:
                return {"success": False, "message": "Invalid image data"}

            # Convert numpy array to PIL Image
            image_pil = Image.fromarray(image)
            
            # Detect face and get bounding boxes
            boxes, _ = self.mtcnn.detect(image_pil)
            
            if boxes is None or len(boxes) == 0:
                return {"success": False, "message": "No face detected in image"}
            
            if len(boxes) > 1:
                return {"success": False, "message": "Multiple faces detected"}

            # Get face embedding
            face = self.mtcnn(image_pil)
            if face is None:
                return {"success": False, "message": "Could not extract face"}

            # Get embedding
            with torch.no_grad():
                embedding = self.resnet(face.unsqueeze(0).to(self.device))
                encoding = embedding[0].cpu().numpy()

            return {
                "success": True,
                "encoding": encoding,
                "location": boxes[0].tolist()
            }

        except Exception as e:
            print(f"Face extraction error: {str(e)}")
            return {"success": False, "message": f"Error processing image: {str(e)}"}

    def add_face(self, face_encoding, employee_id: int, name: str) -> bool:
        try:
            self.known_faces[employee_id] = {
                "encoding": face_encoding,
                "name": name
            }
            self.save_known_faces()
            return True
        except Exception as e:
            print(f"Error adding face: {e}")
            return False

    def recognize_face(self, image_data: str) -> Dict:
        try:
            image = self._base64_to_image(image_data)
            # Convert numpy array to PIL Image
            image_pil = Image.fromarray(image)
            
            # Detect face and get bounding boxes
            boxes, _ = self.mtcnn.detect(image_pil)
            
            if boxes is None or len(boxes) == 0:
                return {"success": False, "message": "No face detected in image"}
            
            # Get face embedding
            face = self.mtcnn(image_pil)
            if face is None:
                return {"success": False, "message": "Could not extract face"}

            # Get embedding
            with torch.no_grad():
                embedding = self.resnet(face.unsqueeze(0).to(self.device))
                unknown_encoding = embedding[0].cpu().numpy()

            # Compare with known faces
            for employee_id, face_data in self.known_faces.items():
                if self.compare_faces(face_data["encoding"], unknown_encoding):
                    return {
                        "success": True,
                        "employee_id": employee_id,
                        "name": face_data["name"],
                        "confidence": self.compare_faces_with_confidence(face_data["encoding"], unknown_encoding)
                    }

            return {"success": False, "message": "Face not recognized"}

        except Exception as e:
            print(f"Error in face recognition: {e}")
            return {"success": False, "message": str(e)}

    def detect_faces(self, image_data: str) -> Dict:
        try:
            image = self._base64_to_image(image_data)
            if image is None:
                return {"success": False, "message": "Invalid image data"}

            image_pil = Image.fromarray(image)
            boxes, _ = self.mtcnn.detect(image_pil)

            if boxes is None or len(boxes) == 0:
                return {
                    "success": True,
                    "faces": [],
                    "message": "No faces detected in image"
                }
            
            faces = [
                {
                    "left": int(box[0]),
                    "top": int(box[1]),
                    "right": int(box[2]),
                    "bottom": int(box[3])
                }
                for box in boxes
            ]
            
            return {
                "success": True,
                "faces": faces,
                "message": f"Found {len(faces)} face(s)"
            }
        except Exception as e:
            print(f"Error in face detection: {e}")
            return {"success": False, "message": str(e)}

    def compare_faces(self, known_encoding, unknown_encoding, tolerance=0.7):
        try:
            # Convert to numpy arrays if they're not already
            known = np.array(known_encoding)
            unknown = np.array(unknown_encoding)
            
            # Calculate Euclidean distance
            distance = np.linalg.norm(known - unknown)
            return distance < tolerance
        except Exception as e:
            print(f"Error comparing faces: {e}")
            return False

    def compare_faces_with_confidence(self, known_encoding, unknown_encoding) -> float:
        try:
            # Convert to numpy arrays if they're not already
            known = np.array(known_encoding)
            unknown = np.array(unknown_encoding)
            
            # Calculate Euclidean distance and convert to similarity score
            distance = np.linalg.norm(known - unknown)
            # Convert distance to similarity score (0 to 1)
            similarity = 1 / (1 + distance)
            return float(similarity)
        except Exception as e:
            print(f"Error comparing faces: {e}")
            return 0.0

    def _base64_to_image(self, base64_string: str) -> Optional[np.ndarray]:
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Remove whitespace and newlines
            base64_string = base64_string.strip()
            
            # Add padding if needed
            missing_padding = len(base64_string) % 4
            if missing_padding:
                base64_string += '=' * (4 - missing_padding)

            # Decode base64
            img_data = base64.b64decode(base64_string)
            nparr = np.frombuffer(img_data, np.uint8)
            
            # Decode image
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Failed to decode image")

            # Check image dimensions
            if image.shape[0] == 0 or image.shape[1] == 0:
                raise ValueError("Image has invalid dimensions")
                
            # Convert to RGB
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        except Exception as e:
            print(f"Error converting base64 to image: {str(e)}")
            return None

# Initialize the system
face_system = FaceRecognitionSystem()
