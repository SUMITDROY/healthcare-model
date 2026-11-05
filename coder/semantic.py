"""Local ONNX E5 inference. No model-hub client and no runtime downloads."""

from functools import lru_cache
import json
import os
from pathlib import Path

import numpy as np


class SemanticIndex:
    def __init__(self, directory):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.directory = Path(directory)
        self.tokenizer = Tokenizer.from_file(str(self.directory / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=256)
        self.tokenizer.enable_padding(pad_id=1, pad_token="<pad>")
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(
            str(self.directory / "model_quantized.onnx"),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        self.input_names = {x.name for x in self.session.get_inputs()}
        self.vectors = None
        self.codes = None
        if (self.directory / "categories.npy").exists():
            self.vectors = np.load(self.directory / "categories.npy", mmap_mode="r")
            self.codes = json.loads((self.directory / "codes.json").read_text())

    def encode(self, texts, prefix="query: ", batch_size=16):
        vectors = []
        for start in range(0, len(texts), batch_size):
            encoded = self.tokenizer.encode_batch(
                [prefix + s for s in texts[start : start + batch_size]]
            )
            ids = np.asarray([e.ids for e in encoded], dtype=np.int64)
            mask = np.asarray([e.attention_mask for e in encoded], dtype=np.int64)
            inputs = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self.input_names:
                inputs["token_type_ids"] = np.zeros_like(ids)
            output = self.session.run(None, inputs)[0]
            if output.ndim == 3:
                expanded = mask[..., None].astype(np.float32)
                output = (output * expanded).sum(axis=1) / expanded.sum(axis=1).clip(1)
            output = output.astype(np.float32)
            output /= np.linalg.norm(output, axis=1, keepdims=True).clip(1e-12)
            vectors.append(output)
        return np.concatenate(vectors)

    @lru_cache(maxsize=1024)
    def query(self, text):
        return self.encode([text])[0]


@lru_cache(maxsize=2)
def load_index(directory):
    return SemanticIndex(directory)


def available_index(enabled=False):
    if not enabled:
        return None
    directory = Path(
        os.environ.get("CODER_SEMANTIC_DIR", "artifacts/semantic")
    ).resolve()
    if not (directory / "categories.npy").exists():
        return None
    return load_index(str(directory))
