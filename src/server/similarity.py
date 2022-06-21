from random import shuffle
from functools import lru_cache
from flask import Blueprint, render_template, abort, Response, jsonify, request, make_response

from src import Fred
from src.server import image_features
from src.server.utils import NumpyEncoder

similarity_getter = Fred(features_list=image_features)


similarity_routes = Blueprint('similarity_routes', __name__)
similarity_routes.json_encoder = NumpyEncoder


@similarity_routes.route('/similarity/neighbors/<int:image_id>')
@lru_cache(2500)
def get_neighbors(image_id):
    feature_vector = image_features[image_id].features
    distances, index = similarity_getter.nearest_neighbors(feature_vector, 25)
    index = [i for i in index[0] if i != image_id]

    image_datas = [similarity_getter.qp.get_matched_for_image(i) for i in index]
    human_tags = similarity_getter.qp.tag_manager.get_tags_for_indices(index)

    # need to do this in 2 steps so we don't fudge things up
    for image_data, (idx, human_tag_set) in zip(image_datas, human_tags.items()):
        # if not idx == image_data['image']:
        #     raise ValueError
        image_data['humanTags'] = human_tag_set
    return jsonify({'neighbors': image_datas})


@similarity_routes.route('/benchSimilarity', methods=['POST'])
def get_bench_similarity():
    params = request.get_json()
    ids = params.get('imageIDs', [])
    n = params.get('n', 20 if len(ids) < 5 else 10)

    if not ids:
        return make_response(jsonify({'reason': 'need to specify imageIDs'}), 400)

    index = []
    for image_id in ids:
        feature_vector = image_features[image_id].features
        distances, this_index = similarity_getter.nearest_neighbors(feature_vector, n)
        # index += [i for i in this_index[0] if i != image_id]
        index += list(this_index[0])

    index = list(set([i for i in index if i not in ids]))[:25]

    shuffle(index)

    image_datas = [similarity_getter.qp.get_matched_for_image(i) for i in index]
    human_tags = similarity_getter.qp.tag_manager.get_tags_for_indices(index)

    # need to do this in 2 steps so we don't fudge things up
    for image_data, (idx, human_tag_set) in zip(image_datas, human_tags.items()):
        # if not idx == image_data['image']:
        #     raise ValueError
        image_data['humanTags'] = human_tag_set
    return jsonify({'neighbors': image_datas})
