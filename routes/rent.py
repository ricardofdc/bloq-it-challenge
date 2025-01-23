"""
This file contains the entry points for the '/rent' routes.
More details about how to use them and what they do can be found on the API
specification (`api.yaml`).
"""

from http import HTTPStatus

from flask import request
from markupsafe import escape

from model.rent import RentModel

from . import api, db

rent_model = RentModel(db)

@api.get('/rent')
def get_rent():
    """
    Entry point for GET '/rent' route.
    """
    rent_id = request.args.get('id')
    locker_id = request.args.get('lockerId')
    if rent_id and 'lockerId' in request.args.keys():
        return (
            'You cannot set "id" and "lockerId" parameters together.',
            HTTPStatus.BAD_REQUEST
        )
    if rent_id:
        return rent_model.get_by_id(escape(rent_id))
    if 'lockerId' in request.args.keys():
        return rent_model.get_by_locker_id(escape(locker_id))
    return rent_model.get_all()

@api.post('/rent')
def create_rent():
    """
    Entry point for POST '/rent' route.
    """
    new_rent = request.get_json()
    return rent_model.create(new_rent)

@api.delete('/rent')
def delete_rent():
    """
    Entry point for DELETE '/rent' route.
    """
    rent_id = request.args.get('id')
    if rent_id:
        return rent_model.delete(escape(rent_id))
    return ('Parameter "id" is missing.', HTTPStatus.BAD_REQUEST)

@api.put('/rent/<uuid:rent_id>/send')
def send_rent(rent_id):
    """
    Entry point for PUT '/rent/<uuid:rent_id>/send' route.
    """
    locker_id = request.args.get('toLockerId')
    if locker_id is None:
        return ('Parameter "toLockerId" is missing.', HTTPStatus.BAD_REQUEST)
    return rent_model.send(escape(rent_id), escape(locker_id))

@api.put('/rent/<uuid:rent_id>/dropoff')
def dropoff_rent(rent_id):
    """
    Entry point for PUT '/rent/<uuid:rent_id>/dropoff' route.
    """
    locker_id = request.args.get('toLockerId')
    if locker_id is None:
        return ('Parameter "toLockerId" is missing.', HTTPStatus.BAD_REQUEST)
    return rent_model.dropoff(escape(rent_id), escape(locker_id))

@api.put('/rent/<uuid:rent_id>/pickup')
def pickup_rent(rent_id):
    """
    Entry point for PUT '/rent/<uuid:rent_id>/pickup' route.
    """
    locker_id = request.args.get('fromLockerId')
    if locker_id is None:
        return ('Parameter "fromLockerId" is missing.', HTTPStatus.BAD_REQUEST)
    return rent_model.pickup(escape(rent_id), escape(locker_id))
