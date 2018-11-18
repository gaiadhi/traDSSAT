import json
from copy import deepcopy

import numpy as np
from chardet import UniversalDetector


def write_json(obj, file):
    obj = deepcopy(obj)
    jsonify(obj)
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def read_json(file):
    with open(file, 'r', encoding='utf-8') as f:
        d = json.load(f)
    numpyfiy(d)
    return d


def jsonify(d):
    for k, v in d.items():
        if isinstance(v, np.ndarray):
            d[k] = v.tolist()
        elif isinstance(v, dict):
            jsonify(v)
        elif isinstance(v, list):
            for i in v:
                jsonify(i)


def numpyfiy(d):
    for k, v in d.items():
        if isinstance(v, list):
            d[k] = np.array(v)
        elif isinstance(v, dict):
            jsonify(v)


def detect_encod(file):
    detector = UniversalDetector()
    with open(file, 'rb') as d:
        for i, line in enumerate(d.readlines()):

            detector.feed(line)

            if detector.done:
                break

    detector.close()

    return detector.result['encoding']
