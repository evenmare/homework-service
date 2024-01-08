# pylint: disable=too-few-public-methods,missing-class-docstring
from typing import List, Optional

from ninja import Schema, ModelSchema, Field

from route_settings_builder import models


class LoginSchema(Schema):
    """ Схема для авторизации """
    username: str
    password: str


class LoginResponseSchema(Schema):
    """ Схема для ответа на авторизацию """
    success: bool
    message: str


class PlaceSchema(ModelSchema):
    """ Схема к сущности места """
    longitude: float
    latitude: float

    class Config:
        model = models.Place
        model_fields = ('id', 'name', 'longitude', 'latitude',)


class CriterionSchema(ModelSchema):
    """ Схема к сущности критерия """

    class Config:
        model = models.Criterion
        model_fields = ('id', 'internal_name', 'name', 'value_type',)


class NestedCriterionSchema(Schema):
    """ Схема связи к сущности критерия """
    criterion: CriterionSchema
    value: str


class DetailedPlaceSchema(PlaceSchema):
    """ Схема детализации сущности места """
    criteria: List[NestedCriterionSchema] = Field([], alias='placecriterion_set')

    class Config:
        model = models.Place
        model_fields = ('id', 'name', 'longitude', 'latitude', 'description',)


class ListRouteSchema(ModelSchema):
    """ Схема сущности маршрута для перечня """
    is_draft: bool

    class Config:
        model = models.Route
        model_fields = ('uuid', 'updated_at', 'name',)


class DetailedRouteSchema(ListRouteSchema):
    """ Схема детализации сущности маршрута """
    criteria: List[NestedCriterionSchema] = Field([], alias='routecriterion_set')
    details: Optional[dict]
    places: List[PlaceSchema]
    guide_description: Optional[str]

    class Config:
        model = models.Route
        model_fields = ('uuid', 'updated_at', 'name', 'details', 'places', 'guide_description',)


class NestedSaveRouteCriterionSchema(Schema):
    """ Схема для создания связи критерий – маршрут """
    criterion_id: int
    value: str


class UpdateRouteSchema(Schema):
    """ Схема обновления маршрута """
    name: str
    guide_description: Optional[str] = None
    criteria: Optional[List[NestedSaveRouteCriterionSchema]] = []
    places: Optional[List[int]] = []


class PartialUpdateRouteSchema(UpdateRouteSchema):
    """ Схема частичного обновления маршрута """
    name: Optional[str] = None


class CreateRouteSchema(UpdateRouteSchema):
    """ Схема создания маршрута """
    name: str
    places: Optional[List[int]] = []
