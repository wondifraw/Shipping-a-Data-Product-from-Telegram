"""
image_detection.py
------------------
Scans the data lake for new images, runs YOLOv8 object detection, and stores detection results in the raw.image_detections table in PostgreSQL.

Setup:
- Requires ultralytics (YOLOv8) and database connection info in .env
- Expects images in data/raw/media/channel_name/YYYY-MM-DD/*.jpg

Usage:
    python src/image_detection.py

Example (as a module):
    from image_detection import create_table, detect_and_store
    from database import get_engine
    engine = get_engine()
    create_table(engine)
    detect_and_store(engine)

This script is typically run after loading new images with telegram_scraper.py and data_loader.py.
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
    Args:
        engine: SQLAlchemy engine connected to the target database.
    Returns:
        None
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
    Extracts the message_id from the image filename (assumes format: messageid_timestamp.jpg).
    Args:
        filename (str): Path or name of the image file.
    Returns:
        int or None: Extracted message_id, or None if extraction fails.
    """
    # Assumes filename starts with message_id (e.g., 172676_1752556394.jpg)
    base = os.path.basename(filename)
    try:
        return int(base.split('_')[0])
    except Exception:
        return None

def detect_and_store(engine):
    """
    Runs YOLOv8 on all images in the data lake and stores detection results in the database.
    Each detection is linked to a message_id for downstream analytics.
    Args:
        engine: SQLAlchemy engine connected to the target database.
    Returns:
        None
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
    engine = get_engine()
    create_table(engine)
    detect_and_store(engine) 