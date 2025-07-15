"""
image_detection.py
------------------
Runs YOLOv8 object detection on all images in the data lake and stores results in the raw.image_detections table in PostgreSQL. Handles table creation and logs all actions.
"""
import os
import glob
from ultralytics import YOLO
from sqlalchemy import text
from database import get_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMAGE_ROOT = "data/raw/media"
MODEL_PATH = "yolov8n.pt"  # You can use yolov8s.pt, yolov8m.pt, etc.

def create_table(engine):
    """
    Create the raw.image_detections table if it does not exist.
    This table stores YOLOv8 object detection results for each image.
    """
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE SCHEMA IF NOT EXISTS raw;
            CREATE TABLE IF NOT EXISTS raw.image_detections (
                id SERIAL PRIMARY KEY,
                message_id BIGINT,
                detected_object_class TEXT,
                confidence_score FLOAT
            );
        """))
        conn.commit()

def get_message_id_from_filename(filename):
    """
    Extract the message_id from the image filename.
    Assumes filenames are formatted as <message_id>_...jpg (e.g., 172676_1752556394.jpg).
    Args:
        filename (str): The image file path.
    Returns:
        int or None: The extracted message_id, or None if not found.
    """
    base = os.path.basename(filename)
    try:
        return int(base.split('_')[0])
    except Exception:
        return None

def detect_and_store(engine):
    """
    Run YOLOv8 object detection on all images in IMAGE_ROOT and store results in the database.
    Each detection is linked to a message_id (from the filename) and includes the detected class and confidence score.
    """
    model = YOLO(MODEL_PATH)
    image_files = glob.glob(os.path.join(IMAGE_ROOT, "**", "*.jpg"), recursive=True)
    logger.info(f"Found {len(image_files)} images for detection.")
    with engine.connect() as conn:
        for img_path in image_files:
            message_id = get_message_id_from_filename(img_path)
            if not message_id:
                logger.warning(f"Could not extract message_id from {img_path}")
                continue
            results = model(img_path)
            for r in results:
                for box in r.boxes:
                    class_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = model.names[class_id]
                    # Insert detection result into the database
                    conn.execute(text("""
                        INSERT INTO raw.image_detections (message_id, detected_object_class, confidence_score)
                        VALUES (:message_id, :class_name, :conf)
                    """), {
                        'message_id': message_id,
                        'class_name': class_name,
                        'conf': conf
                    })
        conn.commit()
    logger.info("Image detection complete and results stored.")

if __name__ == "__main__":
    try:
        engine = get_engine()
        create_table(engine)
        detect_and_store(engine)
    except Exception as e:
        logger.error(f"Uncaught exception in main: {e}") 