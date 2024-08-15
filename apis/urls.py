
from django.contrib import admin
from django.urls import path

from apis.views import UserSignUpView, UserLoginView, BooksAPIViewSet, AuthorAPIViewSet, FavoriteBooksAPIViewSet

urlpatterns = [
    # User related APIs
    path('add_user/', UserSignUpView.as_view({"post": "create"}), name='add_user'),
    path("login/", UserLoginView.as_view({"post": "create"}), name="user_login"),

    # Book related APIs
    path("books/", BooksAPIViewSet.as_view({"get": "list"}), name="books"),
    path("book/<int:pk>/", BooksAPIViewSet.as_view({"get": "retrieve"}), name="book"),
    path("add_book/", BooksAPIViewSet.as_view({"post": "create"}), name="add_book"),
    path("update_book/<int:pk>/", BooksAPIViewSet.as_view({"put": "update"}), name="update_book"),
    path("delete_book/<int:pk>/", BooksAPIViewSet.as_view({"delete": "destroy"}), name="delete_book"),

    # Author related APIs
    path("authors/", AuthorAPIViewSet.as_view({"get": "list"}), name="authors"),
    path("author/<int:pk>/", AuthorAPIViewSet.as_view({"get": "retrieve"}), name="author"),
    path("add_author/", AuthorAPIViewSet.as_view({"post": "create"}), name="add_author"),
    path("update_author/<int:pk>/", AuthorAPIViewSet.as_view({"put": "update"}), name="update_author"),
    path("delete_author/<int:pk>/", AuthorAPIViewSet.as_view({"delete": "destroy"}), name="delete_author"),

    # Favourite related APIs
    path("favorites/", FavoriteBooksAPIViewSet.as_view({"get": "list", "post": "create"}), name="favorites-list-create"),
    path("favorites/<int:pk>/", FavoriteBooksAPIViewSet.as_view({"delete": "destroy"}), name="favorites-delete"),

]
