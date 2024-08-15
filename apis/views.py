import random

from django.db.models import Q, Count
from rest_framework.permissions import IsAuthenticated

from apis.models import Book, User, Author
from apis.serializers import BookSerializer, UserSignupSerializer, UserLoginSerializer, AuthorSerializer
from common.response_mixins import BaseAPIView
from rest_framework.viewsets import ModelViewSet

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Book, Favorite
from .serializers import BookSerializer, FavoriteSerializer
class BooksAPIViewSet(BaseAPIView, ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(author__name__icontains=search_query)
            )
        return queryset


class AuthorAPIViewSet(BaseAPIView, ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]


class UserSignUpView(BaseAPIView, ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSignupSerializer
    permission_classes = []

    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = self.serializer_class(data=data, context={"request": request})
            if serializer.is_valid(raise_exception=False):
                serializer.save()
                return self.send_success_response(
                    message="User signed up successfully.",
                    data=serializer.data,
                )
            return self.send_bad_request_response(
                message=serializer.errors,
            )
        except Exception as e:
            return self.send_bad_request_response(
                message=e.args[0],
            )


class UserLoginView(BaseAPIView, ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserLoginSerializer
    permission_classes = []

    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = self.serializer_class(data=data, context={"request": request})
            if serializer.is_valid(raise_exception=False):
                return self.send_success_response(
                    message="User logged in successfully.",
                    data=serializer.data,
                )
            return self.send_bad_request_response(
                message=serializer.errors,
            )
        except Exception as e:
            return self.send_bad_request_response(
                message=e.args[0])


class FavoriteBooksAPIViewSet(ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({"error": "Book ID is required."}, status=400)

        if Favorite.objects.filter(user=user).count() >= 20:
            return Response({"error": "Max of 20 favorite books allowed."}, status=400)

        favorite, created = Favorite.objects.get_or_create(user=user, book_id=book_id)
        if not created:
            return Response({"error": "Book is already in your favorites."}, status=400)

        recommendations = self.get_recommendations(user)
        serializer = self.get_serializer(favorite)
        return Response({
            "favorite": serializer.data,
            "recommendations": BookSerializer(recommendations, many=True).data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=204)

    def get_recommendations(self, user):
        favorite_books = user.favorites.all().values_list('book_id', flat=True)
        if not favorite_books:
            return []

        # Simple similarity algorithm based on common author or genres (can be expanded)
        recommended_books = Book.objects.exclude(id__in=favorite_books).filter(
            Q(author__books__in=favorite_books) |
            Q(title__icontains=random.choice(user.favorites.all()).book.title.split()[0])
        ).distinct().annotate(num_favorites=Count('favorited_by')).order_by('-num_favorites')[:5]

        return recommended_books