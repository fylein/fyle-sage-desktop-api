import logging
from rest_framework import generics
from apps.fyle.serializers import ImportFyleAttributesSerializer

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ImportFyleAttributesView(generics.CreateAPIView):
    """
    Import Fyle Attributes View
    """

    serializer_class = ImportFyleAttributesSerializer
