"""
This file contains the entry points for the '/locker' routes.
More details about how to use them and what they do can be found on the API
specification (`api.yaml`).
"""

from http import HTTPStatus

from flask import request
from markupsafe import escape

from model.locker import LockerModel

from . import api, db

locker_model = LockerModel(db)

@api.get('/locker')
def get_locker():
    """
    Entry point for GET '/locker' route.
    """
    locker_id = request.args.get('id')
    bloq_id = request.args.get('bloqId')
    if locker_id and bloq_id:
        return (
            'You cannot set "id" and "bloqId" parameters together.',
            HTTPStatus.BAD_REQUEST
        )
    if locker_id:
        return locker_model.get_by_id(escape(locker_id))
    if bloq_id:
        return locker_model.get_by_bloq_id(escape(bloq_id))

    return locker_model.get_all()

@api.post('/locker')
def create_locker():
    """
    Entry point for POST '/locker' route.
    """
    new_locker = request.get_json()
    return locker_model.create(new_locker)

@api.put('/locker/<uuid:locker_id>/open')
def open_locker(locker_id):
    """
    Entry point for PUT '/locker/<locker_id>/open' route.
    """
    return locker_model.open(escape(locker_id))

@api.put('/locker/<uuid:locker_id>/close')
def close_locker(locker_id):
    """
    Entry point for PUT '/locker/<locker_id>/close' route.
    """
    return locker_model.close(escape(locker_id))

@api.delete('/locker')
def delete_locker():
    """
    Entry point for DELETE '/locker' route.
    """
    locker_id = request.args.get('id')
    if locker_id:
        return locker_model.delete(escape(locker_id))
    return ('Parameter "id" is missing.', HTTPStatus.BAD_REQUEST)
