"""Torch-free YOLO ONNX CPU inference with letterboxing and NMS."""
from pathlib import Path
import ast
from time import perf_counter
import cv2
import numpy as np
import onnxruntime as ort
from .alarm import Detection

class SmokeDetector:
    def __init__(self, model: Path, input_size=640, confidence=.35, nms_iou=.45, threads=2):
        if not model.is_file():
            raise FileNotFoundError(f"Missing smoke model: {model}. Run: uv run python scripts/fetch_model.py")
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(model), sess_options=options, providers=["CPUExecutionProvider"])
        names = ast.literal_eval(self.session.get_modelmeta().custom_metadata_map.get("names", "{}"))
        if len(names) != 1:
            raise ValueError("Expected a single-class Pyronear smoke model; this export describes other classes")
        self.input = self.session.get_inputs()[0]
        self.size = input_size
        for dimension in self.input.shape[2:]:
            if isinstance(dimension, int) and dimension != input_size:
                raise ValueError(f"ONNX export has fixed input {self.input.shape}; configure input_size={dimension}")
        self.confidence, self.nms_iou = confidence, nms_iou

    def predict(self, frame):
        start = perf_counter()
        h, w = frame.shape[:2]
        scale = min(self.size / w, self.size / h)
        nw, nh = round(w * scale), round(h * scale)
        left, top = (self.size-nw)//2, (self.size-nh)//2
        image = np.full((self.size, self.size, 3), 114, dtype=np.uint8)
        image[top:top+nh, left:left+nw] = cv2.resize(frame, (nw, nh))
        tensor = np.ascontiguousarray(image[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32) / 255
        prepared = perf_counter()
        output = self.session.run(None, {self.input.name: tensor})[0]
        inferred = perf_counter()
        predictions = np.squeeze(output, axis=0)
        # Raw single-class YOLOv8/11 export: [1, 5, anchors], no objectness column.
        if predictions.ndim != 2:
            raise ValueError(f"Unsupported YOLO output shape: {output.shape}")
        if predictions.shape[0] == 5:
            predictions = predictions.T
        if predictions.shape[1] != 5:
            raise ValueError(f"Expected single-class xywh+score export, got {output.shape}")
        selected = predictions[predictions[:, 4] >= self.confidence]
        boxes, scores = [], []
        for cx, cy, bw, bh, score in selected:
            boxes.append([float(cx-bw/2), float(cy-bh/2), float(bw), float(bh)])
            scores.append(float(score))
        detections = []
        indices = cv2.dnn.NMSBoxes(boxes, scores, self.confidence, self.nms_iou)
        for index in np.asarray(indices).reshape(-1):
            x, y, bw, bh = boxes[index]
            box = tuple(float(v) for v in np.clip([(x-left)/scale/w, (y-top)/scale/h, (x+bw-left)/scale/w, (y+bh-top)/scale/h], 0, 1))
            if box[2] > box[0] and box[3] > box[1]:
                detections.append(Detection(box, scores[index]))
        return detections, {"preprocess_ms": (prepared-start)*1000, "inference_ms": (inferred-prepared)*1000, "analysis_ms": (perf_counter()-start)*1000}


def annotate(frame, detections):
    image = frame.copy()
    h, w = image.shape[:2]
    for detection in detections:
        x1, y1, x2, y2 = [round(v * (w if i % 2 == 0 else h)) for i, v in enumerate(detection.box)]
        cv2.rectangle(image, (x1,y1), (x2,y2), (40,180,255), 2)
        cv2.putText(image, f"Duman? {detection.confidence:.2f}", (x1, max(18,y1-7)), cv2.FONT_HERSHEY_SIMPLEX, .6, (40,180,255), 2)
    return image
