from django.shortcuts import render, get_object_or_404

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
# from rest_framework.permissions import AllowAny, IsAuthenticated

# from rest_framework.status import (
# 	HTTP_400_BAD_REQUEST,
# 	HTTP_201_CREATED,
# 	HTTP_200_OK
# 	)
from rest_framework.response import Response

# from rest_framework.generics import (
# 	CreateAPIView,
# 	ListAPIView,
# 	ListCreateAPIView,
# 	RetrieveAPIView,
# 	RetrieveUpdateAPIView,
# 	UpdateAPIView,
# 	)

class CustomAuthToken(ObtainAuthToken):

	def post(self, request, *args, **kwargs):
		serializer = self.serializer_class(data=request.data,
		                               context={'request': request})
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
			depot_manager = "staff"

		return Response({
			"status": "success",
			"status_code": 201,
            'message': message,
      		"data":data,
            "token": token.key,
			"depot_id":depot_id,
			"depot": depot_name,
			"is_staff": user.is_staff
		})
