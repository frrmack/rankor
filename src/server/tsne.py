import random
from flask import Blueprint, jsonify, request

from src.TSNE import TSNEPlotter
from src.server import image_features
from src.server.utils import NumpyEncoder

tsne = TSNEPlotter(features_list=image_features)

tsne_routes = Blueprint('tsne_routes', __name__)

tsne_routes.json_encoder = NumpyEncoder


# todo: should we just precalculate some TSNEs and serialize them?
@tsne_routes.route('/tsne/coords')
def get_coords():
    recalc = request.args.get('recalc', False)
    if recalc:
        tsne.get_TNSE_coords()

    n = int(request.args.get('n', 250))
    coords = tsne.TSNE_mapping
    sample = random.sample(coords, n)
    return jsonify(sample)
