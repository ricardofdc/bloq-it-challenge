"""
This file contains the entry points for the '/bloq' routes.
More details about how to use them and what they do can be found on the API
specification (`api.yaml`).
"""

from http import HTTPStatus

from flask import request
from markupsafe import escape

from model.bloq import BloqModel

from . import api, db

bloq_model = BloqModel(db)

@api.get('/bloq')
def get_bloq():
    """
    Entry point for GET '/bloq' route.
    """
    bloq_id = request.args.get('id')
    if bloq_id:
        return bloq_model.get_by_id(escape(bloq_id))
    return bloq_model.get_all()

@api.post('/bloq')
def create_bloq():
    """
    Entry point for POST '/bloq' route.
    """
    new_bloq = request.get_json()
    return bloq_model.create(new_bloq)

@api.put('/bloq')
def update_bloq():
    """
    Entry point for PUT '/bloq' route.
    """
    new_bloq = request.get_json()
    return bloq_model.update(new_bloq)

@api.delete('/bloq')
def delete_bloq():
    """
    Entry point for DELETE '/bloq' route.
    """
    bloq_id = request.args.get('id')
    if bloq_id:
        return bloq_model.delete(escape(bloq_id))
    return ('Parameter "id" is missing.', HTTPStatus.BAD_REQUEST)
