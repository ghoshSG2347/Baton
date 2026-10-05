from pathlib import PurePosixPath
IGNORED_DIRS={"node_modules",".git","dist","build","coverage","__pycache__",".venv","venv","assets"}
IGNORED_NAMES={"package-lock.json","yarn.lock","pnpm-lock.yaml"}
BINARY_EXTENSIONS={".png",".jpg",".jpeg",".gif",".webp",".ico",".pdf",".zip",".woff",".woff2",".ttf",".mp3",".mp4",".mov",".exe",".bin", ".pt", ".pth", ".pkl", ".pickle", ".onnx", ".pb", ".tflite", ".safetensors", ".ckpt", ".joblib", ".h5", ".hdf5", ".npy", ".npz", ".parquet", ".feather", ".arrow"}
def is_relevant(path:str)->bool:
    p=PurePosixPath(path)
    return not any(part in IGNORED_DIRS for part in p.parts) and p.name not in IGNORED_NAMES and p.suffix.lower() not in BINARY_EXTENSIONS
def is_binary(path:str)->bool: return PurePosixPath(path).suffix.lower() in BINARY_EXTENSIONS
