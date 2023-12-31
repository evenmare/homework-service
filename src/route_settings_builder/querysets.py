from django.db import models


class RouteQuerySet(models.QuerySet):
    """ QuerySet к модели Route """
    def add_is_draft_field(self):
        """
        Добавление поля is_draft в запрос
        :return: QuerySet
        """
        return self.annotate(is_draft=models.Case(models.When(details__isnull=True, then=True),
                                                  default=False))
