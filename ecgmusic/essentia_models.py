"""A second opinion from pretrained Essentia models: four mood classifiers and DEAM valence/arousal."""
import os
import urllib.request

import numpy as np

from . import config

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
_models = {}


def _model_path(key):
    path = config.ESSENTIA_DIR / os.path.basename(config.ESSENTIA_FILES[key])
    if not path.exists():
        config.ESSENTIA_DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(config.ESSENTIA_URL + config.ESSENTIA_FILES[key], path)
    return str(path)


def _load_models():
    import essentia
    essentia.log.infoActive = essentia.log.warningActive = False
    from essentia.standard import TensorflowPredict2D, TensorflowPredictEffnetDiscogs, TensorflowPredictMusiCNN

    _models["effnet"] = TensorflowPredictEffnetDiscogs(graphFilename=_model_path("effnet"), output="PartitionedCall:1")
    _models["musicnn"] = TensorflowPredictMusiCNN(graphFilename=_model_path("musicnn"), output="model/dense/BiasAdd")
    _models["deam"] = TensorflowPredict2D(graphFilename=_model_path("deam"), output="model/Identity")
    for mood in config.MOODS:
        _models[mood] = TensorflowPredict2D(graphFilename=_model_path(mood), output="model/Softmax")


def analyze_wav(path):
    """Mood probabilities (0-1) and DEAM valence/arousal (1-9, where 5 is neutral) of a WAV file."""
    if not _models:
        _load_models()
    from essentia.standard import MonoLoader
    audio = MonoLoader(filename=str(path), sampleRate=16000, resampleQuality=4)()
    effnet = _models["effnet"](audio)
    scores = {mood: float(np.mean(_models[mood](effnet)[:, config.MOOD_COLUMNS[mood]])) for mood in config.MOODS}
    valence, arousal = np.mean(_models["deam"](_models["musicnn"](audio)), axis=0)
    scores.update(valence=float(valence), arousal=float(arousal))
    return scores
