# pylint: disable=abstract-method,missing-class-docstring,too-few-public-methods
from typing import Optional, List
from uuid import UUID

from django.db.models import Q
from ninja import FilterSchema, Field


class PlaceFilterSchema(FilterSchema):
    """ Схема фильтров для списка мест """
    name: Optional[str] = None
    longitude__gte: Optional[float] = None
    longitude__lte: Optional[float] = None
    latitude__gte: Optional[float] = None
    latitude__lte: Optional[float] = None
    criteria: Optional[List[str]] = None
    id__in: Optional[List[int]] = None

    @staticmethod
    def filter_criteria(value: Optional[List[str]]) -> Q:
        """
        Фильтр по критериям
        :param value: список критериев вида ['internal_name:value', ...]
        :return: query
        """
        return _filter_by_criteria('placecriterion__value', value)

    class Meta:
        expression_connector = 'AND'


class CriterionFilterSchema(FilterSchema):
    """" Схема фильтров для перечня критериев """
    name: Optional[str] = Field(None, q='name__icontains')
    internal_name: Optional[str] = Field(None, q='internal_name__icontains')
    value_type: Optional[str] = None

    class Meta:
        expression_connector = 'AND'


class RouteFilterSchema(FilterSchema):
    """ Схема фильтров для списка маршрутов """
    uuid: Optional[UUID] = None
    name: Optional[str] = Field(None, q='name__icontains')
    is_draft: Optional[bool] = None
    criteria: Optional[List[str]] = None
    id__in: Optional[List[int]] = None

    @staticmethod
    def filter_criteria(value: Optional[List[str]]) -> Q:
        """
        Фильтр по критериям
        :param value: список критериев вида ['internal_name:value', ...]
        :return: query
        """
        return _filter_by_criteria('routecriterion__value', value)

    class Meta:
        expression_connector = 'AND'


def _filter_by_criteria(through_field_name: str, filter_criteria: Optional[List[str]]) -> Q:
    """
    Фильтрация по критериям
    :param through_field_name: наименование поля, содержащего значение критерия
    :param filter_criteria: перечень критериев
    :return: query
    """
    query = Q()

    if filter_criteria:
        for criterion in filter_criteria:
            criterion_internal_name, criterion_value = criterion.split(':')
            query &= Q(**{'criteria__internal_name': criterion_internal_name, through_field_name: criterion_value})

    return query
