# -*- coding: utf-8 -*-

# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Workout Manager.  If not, see <http://www.gnu.org/licenses/>.

# Standard Library
from datetime import date

# Django
from django.db.models import (
    Avg,
    Max,
    Min,
)

# Third Party
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

# wger
from wger.weight.api.filtersets import WeightEntryFilterSet
from wger.weight.api.serializers import WeightEntrySerializer
from wger.weight.models import WeightEntry


class WeightEntryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for nutrition plan objects
    """

    serializer_class = WeightEntrySerializer

    is_private = True
    ordering_fields = '__all__'
    filterset_class = WeightEntryFilterSet

    def get_queryset(self):
        """
        Only allow access to appropriate objects
        """
        # REST API generation
        if getattr(self, 'swagger_fake_view', False):
            return WeightEntry.objects.none()

        return WeightEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Set the owner
        """
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Aggregate weight statistics for the current user within a date range.

        Accepts two required query parameters, ``date_from`` and ``date_to``,
        both given as ISO-8601 calendar dates (``YYYY-MM-DD``). The range is
        inclusive of both bounds: entries recorded on ``date_from`` as well as
        on ``date_to`` are part of the aggregation.

        Returns the number of matching entries together with the minimum,
        maximum and average weight over the range. When no entries fall inside
        the range the aggregates are returned as ``null`` and ``count`` is 0.
        """
        date_from = self._parse_date_param(request, 'date_from')
        date_to = self._parse_date_param(request, 'date_to')

        if date_from > date_to:
            raise ValidationError('date_from must not be after date_to')

        entries = self.get_queryset().filter(
            date__date__gte=date_from,
            date__date__lt=date_to,
        )
        aggregates = entries.aggregate(
            minimum=Min('weight'),
            maximum=Max('weight'),
            average=Avg('weight'),
        )

        return Response(
            {
                'date_from': date_from,
                'date_to': date_to,
                'count': entries.count(),
                'min': aggregates['minimum'],
                'max': aggregates['maximum'],
                'average': aggregates['average'],
            }
        )

    @staticmethod
    def _parse_date_param(request, name):
        """
        Read and parse a required ISO date query parameter.

        Raises a validation error (HTTP 400) if the parameter is missing or is
        not a valid ``YYYY-MM-DD`` date, so that malformed input is rejected
        instead of being silently ignored.
        """
        raw_value = request.query_params.get(name)
        if not raw_value:
            raise ValidationError(f'{name} is a required query parameter')

        try:
            return date.fromisoformat(raw_value)
        except ValueError:
            raise ValidationError(f'{name} must be an ISO date (YYYY-MM-DD)')
