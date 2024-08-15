from django.contrib.auth.models import AbstractUser
from django.db import models

from common.model_mixins import TimestampMixin


class User(AbstractUser):
    gender = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=50)


class Author(TimestampMixin):
    id = models.CharField(max_length=500, primary_key=True)
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=500, blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    ratings_count = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    text_reviews_count = models.IntegerField(default=0)
    work_ids = models.JSONField(default=list)
    book_ids = models.JSONField(default=list)
    works_count = models.IntegerField(default=0)
    fans_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Book(TimestampMixin):
    id = models.CharField(max_length=500, primary_key=True)
    title = models.CharField(max_length=500)
    authors = models.ManyToManyField(Author, related_name='books')
    published_date = models.DateField(blank=True, null=True)  # Allow null values
    isbn = models.CharField(max_length=130, unique=True)
    description = models.TextField(blank=True, null=True)
    tsv_description = models.TextField(blank=True, null=True)
    tsv_title = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class Favorite(models.Model):
    user = models.ForeignKey(User, related_name='favorites', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, related_name='favorited_by', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
