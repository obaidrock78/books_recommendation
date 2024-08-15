import json

from django.core.management.base import BaseCommand
from apis.models import Author
from django.db import transaction


class Command(BaseCommand):
    help = 'Import data from authors.json'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='The path to the JSON file to be imported')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        # Initialize a list to batch process
        batch_size = 1000  # Adjust batch size as needed
        batch = []

        with open(file_path, 'r') as file:
            try:
                for line in file:
                    # Load each line as a separate JSON object
                    item = json.loads(line.strip())

                    # Extract data from the JSON object
                    author_id = item.get('id')
                    name = item.get('name')
                    gender = item.get('gender', '')
                    image_url = item.get('image_url', '')
                    about = item.get('about', '')
                    ratings_count = item.get('ratings_count', 0)
                    average_rating = item.get('average_rating', 0.0)
                    text_reviews_count = item.get('text_reviews_count', 0)
                    work_ids = item.get('work_ids', [])
                    book_ids = item.get('book_ids', [])
                    works_count = item.get('works_count', 0)
                    fans_count = item.get('fans_count', 0)

                    # Append to batch list
                    batch.append(
                        Author(
                            id=author_id,
                            name=name,
                            gender=gender,
                            image_url=image_url,
                            about=about,
                            ratings_count=ratings_count,
                            average_rating=average_rating,
                            text_reviews_count=text_reviews_count,
                            work_ids=work_ids,
                            book_ids=book_ids,
                            works_count=works_count,
                            fans_count=fans_count
                        )
                    )

                    # Process the batch if it's full
                    if len(batch) >= batch_size:
                        self._process_batch(batch)
                        batch = []  # Clear batch list for the next set

                # Process any remaining records in the batch
                if batch:
                    self._process_batch(batch)

            except json.JSONDecodeError as e:
                self.stderr.write(self.style.ERROR(f"Failed to decode JSON object: {e}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))

        self.stdout.write(self.style.SUCCESS(f'Data imported successfully from {file_path}'))

    def _process_batch(self, batch):
        try:
            with transaction.atomic():  # Ensure the operation is atomic
                Author.objects.bulk_create(batch, ignore_conflicts=True)  # Use bulk_create to optimize database writes
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to process batch: {e}"))
