import json

import numpy as np


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.float32, np.float64, np.int64)):
            return obj.item()
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)
