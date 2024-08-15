import json
from django.core.management.base import BaseCommand
from django.db import transaction
from apis.models import Author, Book
from datetime import datetime


class Command(BaseCommand):
    help = 'Import data from books.json'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='The path to the JSON file to be imported')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        batch_size = 1000  # Process 1000 records per batch
        batch = []
        author_ids = set()
        book_authors = []

        with open(file_path, 'r') as file:
            try:
                for line in file:
                    item = json.loads(line.strip())

                    # Extract data from the JSON object
                    book_id = item.get('id')
                    title = item.get('title')
                    authors_data = item.get('authors', [])
                    published_date = item.get('publication_date', '')
                    isbn = item.get('isbn13', '') or item.get('isbn', '')
                    description = item.get('description', '')

                    # Collect author IDs
                    for author_data in authors_data:
                        author_id = author_data.get('id')
                        if author_id:
                            author_ids.add(author_id)
                            book_authors.append((book_id, author_id))

                    # Add book to the batch
                    batch.append(
                        Book(
                            id=book_id,
                            title=title,
                            published_date=self.parse_date(published_date),
                            isbn=isbn,
                            description=description
                        )
                    )

                    # Process the batch if it's full
                    if len(batch) >= batch_size:
                        self._process_batch(batch, author_ids, book_authors)
                        batch = []  # Clear batch list for the next set
                        author_ids.clear()  # Clear author IDs for the next set
                        book_authors.clear()  # Clear author mapping for the next set

                # Process any remaining records in the batch
                if batch:
                    self._process_batch(batch, author_ids, book_authors)

            except json.JSONDecodeError as e:
                self.stderr.write(self.style.ERROR(f"Failed to decode JSON object: {e}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))

        self.stdout.write(self.style.SUCCESS(f'Data imported successfully from {file_path}'))

    def _process_batch(self, batch, author_ids, book_authors):
        try:
            with transaction.atomic():
                # Create or update books in bulk
                Book.objects.bulk_create(batch, ignore_conflicts=True)

                # Fetch all authors
                authors = Author.objects.filter(id__in=author_ids).values_list('id', flat=True)
                author_dict = {author_id: Author.objects.get(pk=author_id) for author_id in authors}

                # Update authors for books
                for book_id, author_id in book_authors:
                    if author_id in author_dict:
                        book = Book.objects.get(pk=book_id)
                        book.authors.add(author_dict[author_id])
                        book.save()

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to process batch: {e}"))

    def parse_date(self, date_str):
        """Parse date string to a date object. Returns None if parsing fails."""
        formats = ['%Y-%m-%d', '%Y-%m', '%Y']
        for fmt in formats:
            try:
                if date_str:
                    # If the date format is YYYY-MM, set day to 01
                    if fmt == '%Y-%m' and len(date_str) == 7:
                        return datetime.strptime(date_str + '-01', fmt + '-%d').date()
                    # If the date format is YYYY, set month and day to 01
                    elif fmt == '%Y' and len(date_str) == 4:
                        return datetime.strptime(date_str + '-01-01', fmt + '-%m-%d').date()
                    else:
                        return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None
