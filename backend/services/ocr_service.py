"""OCR service with a modular interface. Supports paddleocr or tesseract."""

from typing import List, Tuple, Optional

from app.core.config import settings


class OCRResult:
    def __init__(self, text: str, confidence: Optional[float], box: Optional[Tuple[int, int, int, int]]):
        self.text = text
        self.confidence = confidence
        self.box = box  # (x1, y1, x2, y2)


class OCRService:
    """Abstracts the OCR engine behind a common interface."""

    def __init__(self, engine: Optional[str] = None):
        self.engine = engine or settings.OCR_ENGINE
        self._reader = None

    def _get_reader(self):
        if self._reader is not None:
            return self._reader
        if self.engine == "paddleocr":
            from paddleocr import PaddleOCR
            self._reader = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        elif self.engine == "tesseract":
            import pytesseract  # noqa: F401
            self._reader = "tesseract"
        else:
            raise ValueError(f"Unsupported OCR engine: {self.engine}")
        return self._reader

    def extract_text(self, image_path: str) -> List[OCRResult]:
        """Extract text regions from an image."""
        reader = self._get_reader()
        results: List[OCRResult] = []

        if self.engine == "paddleocr":
            raw = reader.ocr(image_path, cls=True)
            for page in raw or []:
                if not page:
                    continue
                for line in page:
                    box, (text, conf) = line
                    x_coords = [p[0] for p in box]
                    y_coords = [p[1] for p in box]
                    results.append(
                        OCRResult(
                            text=text,
                            confidence=float(conf),
                            box=(int(min(x_coords)), int(min(y_coords)), int(max(x_coords)), int(max(y_coords))),
                        )
                    )
        elif self.engine == "tesseract":
            import pytesseract
            from PIL import Image
            image = Image.open(image_path)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            n_boxes = len(data["text"])
            for i in range(n_boxes):
                text = data["text"][i].strip()
                if not text:
                    continue
                conf = float(data["conf"][i]) if data["conf"][i] != "-1" else None
                results.append(
                    OCRResult(
                        text=text,
                        confidence=(conf / 100.0) if conf is not None else None,
                        box=(
                            int(data["left"][i]),
                            int(data["top"][i]),
                            int(data["left"][i] + data["width"][i]),
                            int(data["top"][i] + data["height"][i]),
                        ),
                    )
                )
        return results

    def extract_full_text(self, image_path: str) -> str:
        """Return all OCR text joined into a single string (raw output preserved)."""
        results = self.extract_text(image_path)
        return "\n".join(r.text for r in results if r.text)
