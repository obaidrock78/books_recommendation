import ast
import random
from datetime import datetime

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
import faiss
from django.db import connection

from apis.models import Book
from django.db.models import Q, Count
from rest_framework.permissions import IsAuthenticated
import numpy as np
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
                Q(title__icontains=search_query)
            )
        return queryset[:10]


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
        # if not created:
        #     return Response({"error": "Book is already in your favorites."}, status=400)

        recommendations = self.get_recommendations(favorite.book.tsv_description)
        serializer = self.get_serializer(favorite)
        return Response({
            "favorite": serializer.data,
            "recommendations": BookSerializer(recommendations, many=True).data
        })

    def get_recommendations(self, favorite_descriptions):
        start_time = datetime.now()
        print(f"start time {start_time}")
        if isinstance(favorite_descriptions, str):
            favorite_descriptions = [favorite_descriptions]

        # Escape special characters and join descriptions into a tsquery format
        def format_query(descriptions):
            formatted_descriptions = []
            for desc in descriptions:
                # Escape single quotes and format as tsquery term
                formatted_desc = desc.replace("'", "''")
                formatted_descriptions.append(f"'{formatted_desc}'")
            return ' & '.join(formatted_descriptions)

        ts_query = format_query(favorite_descriptions)

        # Perform the search using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, ts_rank(tsv_description, plainto_tsquery(%s)) AS rank
                FROM apis_book
                WHERE ts_rank(tsv_description, to_tsquery(%s)) > 0
                ORDER BY rank DESC
                LIMIT 5
            """, [ts_query, ts_query])

            results = cursor.fetchall()

        # Fetch recommended books
        recommended_books = []
        for book_id, title, rank in results:
            book = Book.objects.get(id=book_id)
            recommended_books.append(book)
        print(f"end time {datetime.now() - start_time}")
        return recommended_books

    # def get_recommendations(self, favorite_descriptions):
    #     # Fetch books and their descriptions
    #     books = list(Book.objects.all())  # Convert QuerySet to list
    #     all_books = [book.description for book in books]
    #     if isinstance(favorite_descriptions, str):
    #         favorite_descriptions = [favorite_descriptions]
    #
    #     # Load or initialize the TF-IDF vectorizer
    #     vectorizer = TfidfVectorizer()
    #
    #     # Fit the vectorizer on all book descriptions
    #     vectorizer.fit(all_books)
    #
    #     # Transform favorite descriptions and all books to TF-IDF vectors
    #     favorite_vectors = vectorizer.transform(favorite_descriptions)
    #     all_vectors = vectorizer.transform(all_books)
    #
    #     # Compute cosine similarity
    #     cosine_sim = linear_kernel(favorite_vectors, all_vectors)
    #     avg_similarities = cosine_sim.mean(axis=0)
    #
    #     # Get top 5 book indices with highest similarity
    #     similar_books_indices = avg_similarities.argsort()[-5:][::-1]
    #
    #     # Fetch books from list
    #     recommended_books = [books[i] for i in similar_books_indices]
    #
    #     return recommended_books

    # def get_recommendations(self, favorite_descriptions):
    #     # Fetch all books and their precomputed TF-IDF vectors
    #     all_books = list(Book.objects.filter(description__isnull=False)[:100])  # Convert QuerySet to list
    #     all_vectors = np.array([book.tsv_description for book in all_books if book.tsv_description])
    #
    #     # Convert favorite_descriptions to a NumPy array if not already
    #     if not isinstance(favorite_descriptions, np.ndarray):
    #         favorite_descriptions = np.array(favorite_descriptions)
    #
    #     vectorizer = TfidfVectorizer()
    #     vectorizer.fit(all_vectors)
    #     vectorizer.fit(favorite_descriptions)
    #
    #     # Calculate similarity between favorite_vectors and all_vectors
    #     similarities = cosine_similarity(favorite_descriptions, all_vectors)
    #
    #     # Get indices of books with highest similarity
    #     similar_books_indices = similarities.argmax(axis=1)
    #
    #     # Fetch the recommended books based on similarity
    #     recommended_books = [all_books[i] for i in similar_books_indices]
    #
    #     return recommended_books

    # def get_recommendations(self, favorite_descriptions):
    #     if isinstance(favorite_descriptions, str):
    #         favorite_descriptions = [favorite_descriptions]
    #
    #     # Get all book descriptions
    #     all_books = list(Book.objects.all())
    #     all_descriptions = [book.description for book in all_books]
    #
    #     # Combine all descriptions for TF-IDF
    #     tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
    #     tfidf_matrix = tfidf.fit_transform(all_descriptions).toarray()
    #
    #     # Build FAISS index
    #     index = faiss.IndexFlatL2(tfidf_matrix.shape[1])
    #     index.add(tfidf_matrix)
    #
    #     # Transform favorite descriptions
    #     favorite_matrix = tfidf.transform(favorite_descriptions).toarray()
    #
    #     # Search in FAISS index
    #     D, I = index.search(favorite_matrix, 5)  # Get top 5 matches for each favorite
    #
    #     # Fetch books from list
    #     recommended_books = [all_books[i] for i in I.flatten()]
    #
    #     return recommended_books
