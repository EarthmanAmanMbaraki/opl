from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

class CustomAuthToken(ObtainAuthToken):
    """A view to return a token and information about a user
    """

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        token= Token.objects.get(user=user)
        data = {}
        data["id"] = user.id
        data["email"] = user.email
        data["first_name"] = user.first_name
        data["last_name"] = user.last_name
        message = "Logged in successfully"

        # GET DEPOT ID
        try:
            depot_manager = user.depotmanager_set.last()
            depot_id = depot_manager.depot.id
            depot_name = depot_manager.depot.name
        except:
            depot_id = None
            depot_name = "staff"

        return Response({
            "status": status.HTTP_200_OK,
            'message': message,
            "data":data,
            "token": token.key,
            "depot_id":depot_id,
            "depot": depot_name,
            "is_staff": user.is_staff
        })
