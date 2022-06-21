import io
import base64
from time import time
from functools import lru_cache
from flask import Blueprint, render_template, abort, Response

from src.server import image_features


images_routes = Blueprint('images_routes', __name__)


@images_routes.route('/images/<int:image_id>')
def get_image(image_id):
    # start = time()
    features = image_features[image_id]
    # print(features.image_small)
    img = features.load_image_small()

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    # end = time()
    # print('took', end-start)
    return Response(buffer.getvalue(), mimetype='image/jpeg')
    # return str(image_features[image_id].path)


@images_routes.route('/images/thumbnailRaw/<int:image_id>')
@lru_cache(maxsize=2500)
def get_thumbnail_raw(image_id):
    features = image_features[image_id]
    # print(features.image_small)
    img = features.load_thumbnail()

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    data64 = base64.b64encode(buffer.getvalue())
    return u'data:img/jpeg;base64,' + data64.decode('utf-8')
    # end = time()
    # print('took', end-start)
    # return Response(buffer.getvalue(), mimetype='image/jpeg')


@images_routes.route('/images/thumbnail/<int:image_id>')
@lru_cache(maxsize=2500)
def get_thumbnail(image_id):
    features = image_features[image_id]
    # print(features.image_small)
    img = features.load_thumbnail()

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    # data64 = base64.b64encode(buffer.getvalue())
    # return u'data:img/jpeg;base64,' + data64.decode('utf-8')
    # end = time()
    # print('took', end-start)
    return Response(buffer.getvalue(), mimetype='image/jpeg')
