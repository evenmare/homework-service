import uuid
import json

import pytest

from asgiref.sync import sync_to_async

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client, AsyncClient

from route_settings_builder import models

api_client = Client()
async_api_client = AsyncClient()

pytestmark = pytest.mark.django_db


async def test_health_api():
    """ GET /api/v1/health """
    response = api_client.get(reverse('api:get_health_status'))

    assert response.status_code == 200
    assert {'status': True}


# TODO: Тесты для фильтрации
def test_get_places(auth_credentials):
    """ GET /api/v1/places """
    assert api_client.login(**auth_credentials)

    # Подготовка данных для тестирования
    models.Place.objects.all().delete()

    places = [models.Place(name=f'Место {i}', longitude=90 - i, latitude=90 + i) for i in range(3)]
    places = models.Place.objects.bulk_create(places)

    # Отправка запроса
    response = api_client.get(reverse('api:get_places'))

    # Валидация ответа
    assert response.status_code == 200

    response_data = response.json()
    assert response_data['count'] == 3

    for i, item in enumerate(response_data['items']):
        place = places[i]
        assert item == {
            'id': place.id,
            'name': place.name,
            'longitude': place.longitude,
            'latitude': place.latitude,
        }


def test_get_place(auth_credentials):
    """ GET /api/v1/places/<:id> """
    assert api_client.login(**auth_credentials)

    place = models.Place.objects.create(name='Место детализация', longitude=30.5, latitude=20.4)
    criterion = models.Criterion.objects.create(name='Критерий для детализации', internal_name='place_details')
    place_criterion = models.PlaceCriterion.objects.create(place=place, criterion=criterion, value='some example')

    response = api_client.get(reverse('api:get_place', kwargs={'place_id': place.id}))
    assert response.status_code == 200

    response_data = response.json()
    assert response_data == {
        'id': place.id,
        'name': place.name,
        'longitude': float(place.longitude),
        'latitude': float(place.latitude),
        'criteria': [
            {
                'criterion': {
                    'id': criterion.id,
                    'internal_name': criterion.internal_name,
                    'name': criterion.name,
                    'value_type': criterion.value_type,
                },
                'value': place_criterion.value,
            }
        ]
    }


def test_get_place__not_found(auth_credentials):
    """ GET /api/v1/places/<:id> 404 """
    assert api_client.login(**auth_credentials)

    response = api_client.get(reverse('api:get_place', kwargs={'place_id': 10102314}))
    assert response.status_code == 404


# TODO: Тесты для фильтрации
def test_get_criteria(auth_credentials):
    """ GET /api/v1/criteria """
    assert api_client.login(**auth_credentials)

    models.Criterion.objects.all().delete()

    criteria = [models.Criterion(internal_name=f'specific_{i}', name=f'Специфичный {i}')
                for i in range(3)]
    criteria = models.Criterion.objects.bulk_create(criteria)

    response = api_client.get(reverse('api:get_criteria'))
    assert response.status_code == 200

    response_data = response.json()
    assert len(response_data) == 3

    for i, item in enumerate(response_data):
        assert item == {
            'id': criteria[i].id,
            'internal_name': criteria[i].internal_name,
            'name': criteria[i].name,
            'value_type': criteria[i].value_type,
        }


# TODO: Тесты для фильтрации
def test_get_routes(auth_credentials):
    """ GET /api/v1/routes """
    assert api_client.login(**auth_credentials)

    models.Route.objects.all().delete()

    author = get_user_model().objects.get(username=auth_credentials['username'])

    routes = [models.Route(name=f'Маршрут №{i}', author=author) for i in range(3)]
    routes[0].details = {'some_details': 'info'}
    routes = models.Route.objects.bulk_create(routes)

    response = api_client.get(reverse('api:get_routes'))
    assert response.status_code == 200

    response_data = response.json()
    assert response_data['count'] == 3

    for i, item in enumerate(response_data['items']):
        item.pop('updated_at')
        assert item == {
            'uuid': str(routes[i].uuid),
            'name': routes[i].name,
            'is_draft': False if i == 0 else True,
        }


def test_get_routes__created_by_other_user(auth_credentials):
    """ GET /api/v1/routes для получения данных других пользователей """
    assert api_client.login(**auth_credentials)

    models.Route.objects.all().delete()

    user = get_user_model().objects.create(username='fake')
    models.Route.objects.create(name='Чужой маршрут', author=user)

    response = api_client.get(reverse('api:get_routes'))
    assert response.status_code == 200

    assert response.json()['count'] == 0


def test_get_route(auth_credentials):
    """ GET /api/v1/routes/<:route_uuid> """
    assert api_client.login(**auth_credentials)

    author = get_user_model().objects.get(username=auth_credentials['username'])
    route = models.Route.objects.create(name='Детализация маршрут', author=author, details={'details': 'info'})

    place = models.Place.objects.create(name='Место для маршрута', longitude=30.5, latitude=20.4)
    models.RoutePlace.objects.create(route=route, place=place)

    criterion = models.Criterion.objects.create(name='Критерий для маршрута', internal_name='route_details')
    route_criterion = models.RouteCriterion.objects.create(route=route, criterion=criterion, value='some example')

    response = api_client.get(reverse('api:get_route', kwargs={'route_uuid': route.uuid}))
    assert response.status_code == 200

    response_data = response.json()
    response_data.pop('updated_at')

    assert response_data == {
        'uuid': str(route.uuid),
        'name': route.name,
        'details': route.details,
        'is_draft': False,
        'criteria': [
            {
                'criterion': {
                    'id': criterion.id,
                    'internal_name': criterion.internal_name,
                    'name': criterion.name,
                    'value_type': criterion.value_type,
                },
                'value': route_criterion.value,
            }
        ],
        'places': [
            {
                'id': place.id,
                'name': place.name,
                'longitude': float(place.longitude),
                'latitude': float(place.latitude),
            }
        ],
        'guide_description': None,
    }


def test_get_route__not_found(auth_credentials):
    """ GET /api/v1/routes/<:route_uuid> 404 """
    assert api_client.login(**auth_credentials)

    response = api_client.get(reverse('api:get_route', kwargs={'route_uuid': uuid.uuid4()}))
    assert response.status_code == 404


def test_get_route__created_by_other_user(auth_credentials):
    """ GET /api/v1/routes/<:route_uuid> by other user """
    assert api_client.login(**auth_credentials)

    user = get_user_model().objects.create(username='fake-2')
    route = models.Route.objects.create(name='Детализация маршрут', author=user, details={'details': 'info'})

    response = api_client.get(reverse('api:get_route', kwargs={'route_uuid': route.uuid}))
    assert response.status_code == 404


def test_create_route(auth_credentials, name: str = 'test route'):
    """ POST /api/v1/routes/ """
    assert api_client.login(**auth_credentials)

    criteria = [models.Criterion(internal_name=f'specific_{i}', name=f'Для маршрута {i}')
                for i in range(3)]
    criteria = models.Criterion.objects.bulk_create(criteria)

    place = models.Place.objects.create(name='Место для маршрута', longitude=30.5, latitude=20.4)

    request_data = {
        'name': name,
        'guide_description': 'some desc',
        'criteria': [
            {'criterion_id': criterion.id, 'value': str(i)} for i, criterion in enumerate(criteria)
        ],
        'places': [place.id],
    }

    response = api_client.post(reverse('api:create_route'), json.dumps(request_data),
                               content_type='application/json')
    assert response.status_code == 201

    response_json = response.json()
    route_id = response_json.pop('uuid')
    response_json.pop('updated_at')

    assert response_json == {
        'is_draft': True,
        'name': name,
        'guide_description': 'some desc',
        'criteria': [
            {
                'criterion': {
                    'id': criterion.id,
                    'internal_name': f'specific_{i}',
                    'name': f'Для маршрута {i}',
                    'value_type': 'string',
                },
                'value': str(i),
            } for i, criterion in enumerate(criteria)
        ],
        'details': None,
        'places': [
            {
                'longitude': place.longitude,
                'latitude': place.latitude,
                'id': place.id,
                'name': place.name,
            }
        ]
    }

    route = models.Route.objects.get(uuid=route_id)
    assert set(route.places.all()) == {place}
    assert set(route.criteria.all()) == set(criteria)


def test_update_route(auth_credentials):
    """ PUT /api/v1/routes/{id}/ """
    assert api_client.login(**auth_credentials)

    route_name = 'updatable route'
    test_create_route(auth_credentials, route_name)

    route = models.Route.objects.get(name=route_name)

    new_criterion = models.Criterion.objects.create(name='Критерий для обновления', internal_name='for_update')
    new_place = models.Place.objects.create(name='Место для обновления', longitude=87, latitude=78)

    request_data = {
        'name': 'new name for route',
        'guide_description': 'new desc',
        'criteria': [{
            'criterion_id': new_criterion.id,
            'value': 'new value',
        }],
        'places': [new_place.id]
    }

    response = api_client.put(reverse('api:update_route', kwargs={'route_uuid': str(route.uuid)}),
                              json.dumps(request_data), content_type='application/json')
    assert response.status_code == 200

    response_json = response.json()
    response_json.pop('updated_at')

    assert response_json == {
        'uuid': str(route.uuid),
        'is_draft': True,
        'name': request_data['name'],
        'guide_description': request_data['guide_description'],
        'criteria': [
            {
                'criterion': {
                    'id': new_criterion.id,
                    'internal_name': new_criterion.internal_name,
                    'name': new_criterion.name,
                    'value_type': 'string',
                },
                'value': 'new value',
            },
        ],
        'details': None,
        'places': [
            {
                'longitude': new_place.longitude,
                'latitude': new_place.latitude,
                'id': new_place.id,
                'name': new_place.name,
            }
        ]
    }

    assert set(route.places.all()) == {new_place}
    assert set(route.criteria.all()) == {new_criterion}


def test_partial_update(auth_credentials):
    """ PATCH /api/v1/routes/{id}/ """
    assert api_client.login(**auth_credentials)

    route_name = 'partial updatable route'
    test_create_route(auth_credentials, route_name)

    route = models.Route.objects.get(name=route_name)

    request_data = {
        'name': 'new route name',
    }

    response = api_client.patch(reverse('api:partial_update_route', kwargs={'route_uuid': str(route.uuid)}),
                                json.dumps(request_data), content_type='application/json')
    assert response.status_code == 200

    response_json = response.json()
    response_json.pop('updated_at')

    assert len(response_json.pop('criteria')) == 3
    assert len(response_json.pop('places')) == 1

    assert response_json == {
        'uuid': str(route.uuid),
        'is_draft': True,
        'name': 'new route name',
        'guide_description': 'some desc',
        'details': None,
    }


async def test_remove_route(async_auth_credentials):
    """ DELETE /api/v1/routes/{route_id}/ """
    assert await sync_to_async(async_api_client.login)(**async_auth_credentials)

    route_name = 'remove route'
    await sync_to_async(test_create_route)(async_auth_credentials, route_name)

    route_uuid = (await models.Route.objects.aget(name=route_name)).uuid

    response = await async_api_client.delete(reverse('api:remove_route', kwargs={'route_uuid': route_uuid}))
    assert response.status_code == 204

    assert (await sync_to_async(models.Route.objects.filter(uuid=route_uuid).first)()) is None
