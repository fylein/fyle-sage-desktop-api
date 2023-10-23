from django.db.models import Q
import logging

from rest_framework import generics

from fyle_accounting_mappings.models import DestinationAttribute

from apps.sage300.serializers import Sage300FieldSerializer
from apps.sage300.serializers import ImportSage300AttributesSerializer


logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportSage300AttributesView(generics.CreateAPIView):
    """
    Import Sage300 Attributes View
    """

    serializer_class = ImportSage300AttributesSerializer


class Sage300FieldsView(generics.ListAPIView):
    pagination_class = None
    serializer_class = Sage300FieldSerializer

    def get_queryset(self):
        attribute_types = [
            "VENDOR",
            "ACCOUNT",
            "JOB",
            "CATEGORY",
            "COST_CODE",
            "PAYMENT",
        ]
        attributes = (
            DestinationAttribute.objects.filter(
                ~Q(attribute_type__in=attribute_types),
                workspace_id=self.kwargs["workspace_id"],
            )
            .values("attribute_type", "display_name")
            .distinct()
        )

        serialized_attributes = Sage300FieldSerializer(attributes, many=True).data

        # Adding job by default since we can support importing projects from Sage300 even though they don't exist
        serialized_attributes.append({"attribute_type": "JOB", "display_name": "Job"})

        return serialized_attributes
