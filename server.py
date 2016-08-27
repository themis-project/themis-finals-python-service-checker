# -*- coding: utf-8 -*-
from __future__ import absolute_import
import flask
import redis
import rq
import os
from utils import get_logger
from functools import wraps
from utils import verify_master_token
from worker import queue_push, queue_pull

logger = get_logger()

queue = rq.Queue(connection=redis.Redis(
    host=os.getenv('REDIS_HOST', '127.0.0.1'),
    port=int(os.getenv('REDIS_PORT', '6379')),
    db=int(os.getenv('REDIS_DB', '0'))
))

app = flask.Flask(__name__)
app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False


@app.teardown_request
def teardown_request(exception=None):
    if exception:
        logger.error('Uncaught exception!', exc_info=exception)


def check_api_token(f):
    @wraps(f)
    def func(*args, **kwargs):
        token = flask.request.headers.get(
            os.getenv('THEMIS_FINALS_AUTH_TOKEN_HEADER'),
            None
        )
        if not verify_master_token(token):
            return '', 401
        return f(*args, **kwargs)
    return func


@app.route('/push', methods=['POST'])
@check_api_token
def push():
    payload = flask.request.get_json()
    if payload is None:
        return '', 400
    queue.enqueue(queue_push, payload)
    return '', 202


@app.route('/pull', methods=['POST'])
@check_api_token
def pull():
    payload = flask.request.get_json()
    if payload is None:
        return '', 400
    queue.enqueue(queue_pull, payload)
    return '', 202