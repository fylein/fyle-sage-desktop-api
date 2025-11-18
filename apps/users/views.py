from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.helpers import get_user_profile


class UserProfileView(generics.RetrieveAPIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Get User Details
        """
        employee_profile = get_user_profile(request)
        return Response(
            data=employee_profile,
            status=status.HTTP_200_OK
        )
