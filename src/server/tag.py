from flask import Blueprint, render_template, abort, Response, jsonify, request, make_response

from src.tag import TagManager

tm = TagManager()

tag_routes = Blueprint('tag_routes', __name__)


@tag_routes.route('/addTag', methods=['POST'])
def add_tag():
    params = request.get_json()
    idx = params.get('id')
    tag = params.get('tag')

    if not idx or not tag:
        return make_response(jsonify({'reason': 'need to specify id and tag'}), 400)

    tm.add_tag(idx, tag)
    return jsonify({'success': 'yep!', 'operation': 'add tag'})


@tag_routes.route('/massTag', methods=['POST'])
def mass_tag():
    params = request.get_json()
    ids = params.get('imageIDs')
    tag = params.get('tagName')

    if not ids or not tag:
        return make_response(jsonify({'reason': 'need to specify imageIDs and tagName'}), 400)

    print(ids, tag)
    tm.mass_tag(ids, tag)
    return jsonify({'success': 'yep!', 'operation': 'add tag'})


@tag_routes.route('/removeTag', methods=['POST'])
def remove_tag():
    params = request.get_json()
    idx = params.get('id')
    tag = params.get('tag')

    if not idx or not tag:
        return make_response(jsonify({'reason': 'need to specify id and tag'}), 400)

    tm.remove_tag(idx, tag)
    return jsonify({'success': 'yep!', 'operation': 'remove tag'})


@tag_routes.route('/humanTags/<int:idx>')
def get_tags_for_image(idx):
    tags = tm.get_tags_for_image(idx)
    return jsonify({'image': idx, 'tags': tags})


@tag_routes.route('/saveBench', methods=['POST'])
def save_bench():
    params = request.get_json()
    name = params.get('benchName')
    state = params.get('benchState')

    if not name or not state:
        return make_response(jsonify({'reason': 'need to specify benchName and benchState'}), 400)

    tm.save_bench(name, state)

    return jsonify({'status': 'success'})


def load_bench_by_name(name=None):
    if not name:
        return make_response(jsonify({'reason': 'need to specify benchName'}), 400)

    bench = tm.load_bench(name)
    if not bench:
        return make_response(jsonify({'reason': f'bench {name} not found'}), 400)

    return jsonify({'status': 'success', 'benchState': bench, 'benchName': name})


@tag_routes.route('/loadBench', methods=['POST', 'GET'])
def load_bench():
    if request.method == 'POST':
        params = request.get_json()
        name = params.get('benchName')

    else:
        name = request.args.get('benchName')

    return load_bench_by_name(name)


@tag_routes.route('/deleteBench', methods=['POST', 'GET'])
def delete_bench():
    if request.method == 'POST':
        params = request.get_json()
        name = params.get('benchName')

    else:
        name = request.args.get('benchName')

    if not name:
        return make_response(jsonify({'reason': 'need to specify benchName'}), 400)

    result = tm.delete_bench(name)

    if result != 'deleted':
        return make_response(jsonify({'status': 'failure', 'reason': result}), 400)

    return jsonify({'status': 'success'})


@tag_routes.route('/loadBench/<name>')
def load_bench_cool_route(name):
    return load_bench_by_name(name)


@tag_routes.route('/listBenches')
def list_benches():
    return jsonify({'benchNames': tm.list_benches()})
