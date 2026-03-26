"""FastAPI bridge server connecting Flutter capture requests to ORB recognition."""

from __future__ import annotations

import base64
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from artwork_recognition import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_DB_PATH,
    DEFAULT_IMAGES_DIR,
    DEFAULT_MIN_GOOD_MATCHES,
    DEFAULT_RATIO_TEST,
    ArtworkRecognitionEngine,
)


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8000
MAX_IMAGE_BYTES = 20 * 1024 * 1024


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    """Initialize and close the singleton recognition engine."""
    engine = ArtworkRecognitionEngine(
        db_path=DEFAULT_DB_PATH,
        images_dir=DEFAULT_IMAGES_DIR,
    )
    app.state.engine = engine
    try:
        yield
    finally:
        engine.close()


app = FastAPI(title="Lensa Bridge Server", lifespan=app_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _extract_payload_bytes(image_base64: str) -> bytes:
    """Decode base64 image content and return raw bytes."""
    raw_payload = image_base64.strip()
    if "," in raw_payload:
        raw_payload = raw_payload.split(",", maxsplit=1)[1]

    decoded = base64.b64decode(raw_payload, validate=True)
    if len(decoded) > MAX_IMAGE_BYTES:
        raise ValueError("Decoded image exceeds max size")
    return decoded


def _decode_image_array(image_base64: str) -> np.ndarray:
    """Decode base64 JPEG/PNG bytes into an OpenCV BGR image array."""
    decoded = _extract_payload_bytes(image_base64=image_base64)
    image_buffer = np.frombuffer(decoded, dtype=np.uint8)
    image = cv2.imdecode(image_buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Invalid image payload")
    return image


def _safe_recognize(image_base64: str) -> Dict[str, Any]:
    """Return a stable recognition response, never raising to the caller."""
    try:
        image = _decode_image_array(image_base64=image_base64)
        engine: Optional[ArtworkRecognitionEngine] = getattr(app.state, "engine", None)
        if engine is None:
            return {"found": False}

        result = engine.recognize_from_array(
            image=image,
            confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD,
            ratio_test=DEFAULT_RATIO_TEST,
            min_good_matches=DEFAULT_MIN_GOOD_MATCHES,
        )

        if result is None:
            return {"found": False}

        return {
            "found": True,
            "artwork": result["artwork"],
            "confidence": result["confidence"],
            "good_matches": result["good_matches"],
        }
    except Exception:
        return {"found": False}


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Return bridge health status and artwork count loaded from SQLite."""
    try:
        engine: Optional[ArtworkRecognitionEngine] = getattr(app.state, "engine", None)
        if engine is None:
            return {"status": "ok", "artworks_loaded": 0}
        return {
            "status": "ok",
            "artworks_loaded": engine.get_artworks_count(),
        }
    except Exception:
        return {"status": "ok", "artworks_loaded": 0}


@app.post("/recognize")
async def recognize(request: Request) -> Dict[str, Any]:
    """Recognize an artwork from a base64-encoded image payload."""
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            return {"found": False}
        image_base64 = payload.get("image_base64")
        if not isinstance(image_base64, str):
            return {"found": False}
        return _safe_recognize(image_base64=image_base64)
    except Exception:
        return {"found": False}


if __name__ == "__main__":
    uvicorn.run("bridge_server:app", host=DEFAULT_HOST, port=DEFAULT_PORT, reload=False)
