from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apis.models import Book, User, Author

from rest_framework import serializers
from .models import Book, Favorite


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class FavoriteSerializer(serializers.ModelSerializer):
    book = BookSerializer()

    class Meta:
        model = Favorite
        fields = ['id', 'user', 'book', 'added_at']


class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name")

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """

    password = serializers.CharField(
        trim_whitespace=True,
        max_length=128,
        write_only=True,
    )
    username = serializers.CharField(read_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)

    def validate(self, attrs) -> dict:
        data = self.context["request"].data
        username = data.get("username", None)
        password = data.get("password", None)
        user = authenticate(username=username, password=password)
        token = RefreshToken.for_user(user)

        data = {
            "id": user.id,
            "username": user.username,
            "access_token": str(token.access_token),
            "refresh_token": str(token),
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        return data


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'
