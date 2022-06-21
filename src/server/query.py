from random import shuffle
from flask import Blueprint, render_template, abort, Response, jsonify, request

from src.query import QueryParser
from src.server import image_features
from src.server.utils import NumpyEncoder

qp = QueryParser(image_features)

query_routes = Blueprint('query_routes', __name__)
query_routes.json_encoder = NumpyEncoder


@query_routes.route('/possibleTags')
def possible_tags():
    data = {
        'markets': qp.market_names,
        'tags': qp.tag_names + qp.label_names
    }
    return jsonify(data)


@query_routes.route('/query', methods=['POST'])
def basic_query():
    params = request.get_json()
    n = params.get('n', 100)
    keywords = params.get('keywords', [])
    locations = params.get('locations', [])
    if keywords:
        filtered = qp.query(locations, keywords, keywords, keywords)
    else:
        keywords = tags = params.get('tags', [])
        themes = params.get('themes', [])
        human_tags = params.get('humanTags', [])
        filtered = qp.query(locations, tags, themes, human_tags)

    shuffle(filtered)

    image_datas = [qp.get_matched_for_image(i, keywords) for i in filtered[:n]]
    human_tags = qp.tag_manager.get_tags_for_indices(filtered)

    # need to do this in 2 steps so we don't fudge things up
    for image_data, (idx, human_tag_set) in zip(image_datas, human_tags.items()):
        # if not idx == image_data['image']:
        #     raise ValueError
        image_data['humanTags'] = human_tag_set
    return jsonify({'images': image_datas})


@query_routes.route('/tags', methods=['GET', 'POST'])
def filter_tags():
    if request.method == 'GET':
        counts = qp.get_tag_counts()
    else:
        params = request.get_json()
        if params:
            markets = params.get('markets', [])
            tags = params.get('tags', [])
            labels = params.get('labels', [])
            themes = params.get('themes', [])
            human_tags = params.get('humanTags', [])
            indices = qp.query(markets, tags, themes, human_tags)
        else:
            indices = None
        counts = qp.get_tag_counts(indices)

    out_data = {
        'markets': [{'name': k, 'count': v} for k, v in counts['markets'].items()],
        'tags': [{'name': k, 'count': v} for k, v in counts['tags'].items()],
        'labels': [{'name': k, 'count': v} for k, v in counts['labels'].items()],
        'humanTags': [{'name': k, 'count': v} for k, v in counts['humanTags'].items()],
        'themes': [{'name': k, 'count': v} for k, v in counts['themes'].items()]
    }
    return jsonify(out_data)


@query_routes.route('/tags/<int:idx>')
def get_tags_for_idx(idx):
    feat = qp.features_list[idx]
    human_tags = qp.tag_manager.get_tags_for_image(idx)

    return jsonify({
        'market': feat.market,
        'tags': list(feat.tags.keys()),
        'labels': [feat.label],
        'humanTags': human_tags,
        'themes': feat.themes,
        'image': idx
    })
