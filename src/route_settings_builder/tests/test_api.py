import uuid

import pytest

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client

from route_settings_builder import models

api_client = Client()

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
        ]
    }


def test_get_route__not_found(auth_credentials):
    """ GET /api/v1/routes/<:route_uuid> 404 """
    assert api_client.login(**auth_credentials)

    response = api_client.get(reverse('api:get_route', kwargs={'route_uuid': uuid.uuid4()}))
    assert response.status_code == 404


def test_get_route__created_by_other_user(auth_credentials):
    """ GET /api/v1/routes/<:route_uuid> by other user """
    user = get_user_model().objects.create(username='fake-2')
    route = models.Route.objects.create(name='Детализация маршрут', author=user, details={'details': 'info'})

    response = api_client.get(reverse('api:get_route', kwargs={'route_uuid': route.uuid}))
    assert response.status_code == 401

# TODO: test_create_route, test_update_route, test_partial_route, test_remove_route
# TODO: test_build_route(integration, not integration), test_route_guide
