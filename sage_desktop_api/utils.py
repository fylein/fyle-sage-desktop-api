from rest_framework.serializers import ValidationError
from rest_framework.views import Response


def assert_valid(condition: bool, message: str) -> Response or None:
    """
    Assert conditions
    :param condition: Boolean condition
    :param message: Bad request message
    :return: Response or None
    """
    if not condition:
        raise ValidationError(detail={
            'message': message
        })
