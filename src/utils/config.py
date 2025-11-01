import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

_DEFAULTS: Dict[str, Any] = {
    "detected_faces_dir": "detected_faces",
    "min_detection_interval_seconds": 2,
    "repeat_interval_seconds": 30,
    "recent_seconds": 60,
    "similarity_threshold": 0.6,
    "models_dir": "models",
    "dir_logs": "logs",
    "model_files": {
        "dnn_model": "res10_300x300_ssd_iter_140000.caffemodel",
        "dnn_config": "deploy.prototxt"
    },
    "log_level": "INFO"
}


def _project_root() -> Path:
    # If frozen (pyinstaller), use executable parent; else use two parents up from this file
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[1]


def load_config() -> SimpleNamespace:
    """Load config.json from project root and merge with defaults.

    Returns a SimpleNamespace. Paths are returned as pathlib.Path where appropriate.
    """
    root = _project_root()
    cfg_path = root / 'config.json'
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=logging.INFO)
    cfg: Dict[str, Any] = dict(_DEFAULTS)
    logging.info("Cargando configuración desde: %s", cfg_path.resolve())
    if cfg_path.exists():
        try:
            with cfg_path.open('r', encoding='utf-8') as f:
                file_cfg = json.load(f)
                cfg.update(file_cfg)
        except Exception:
            # If config file is malformed, ignore and use defaults
            pass

    # normalize nested dict for model_files
    if not isinstance(cfg.get('model_files'), dict):
        cfg['model_files'] = _DEFAULTS['model_files']

    # Ensure detected_faces_dir is absolute (project-root relative if relative path)
    ddir = cfg.get('detected_faces_dir') or _DEFAULTS['detected_faces_dir']
    dpath = Path(ddir)
    if not dpath.is_absolute():
        dpath = root / dpath
    cfg['detected_faces_dir'] = dpath.resolve()

    # Ensure models_dir absolute
    mdir = cfg.get('models_dir') or _DEFAULTS['models_dir']
    mpath = Path(mdir)
    if not mpath.is_absolute():
        mpath = root / mpath
    cfg['models_dir'] = mpath.resolve()

    # Ensure dir_logs absolute (project-root relative if needed)
    ldir = cfg.get('dir_logs') or _DEFAULTS['dir_logs']
    lpath = Path(ldir)
    if not lpath.is_absolute():
        lpath = root / lpath
    cfg['dir_logs'] = lpath.resolve()

    # Create directories so app can write assets/logs
    for key in ("detected_faces_dir", "models_dir", "dir_logs"):
        path = cfg.get(key)
        if isinstance(path, Path):
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

    # expose root and return
    cfg['ROOT'] = root

    return SimpleNamespace(**cfg)


# singleton config
config = load_config()
