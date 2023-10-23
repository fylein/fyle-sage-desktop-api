import logging

from rest_framework import generics

from apps.sage300.serializers import ImportSage300AttributesSerializer

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportSage300AttributesView(generics.CreateAPIView):
    """
    Import Sage300 Attributes View
    """

    serializer_class = ImportSage300AttributesSerializer
