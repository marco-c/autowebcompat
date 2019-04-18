import pathlib
import logging

from django.core.management.base import BaseCommand

from app.models import import_dataset, Dataset

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import a dataset from a directory on disk"

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str)
        parser.add_argument('path', type=str)

    def handle(self, slug, path, **options):
        path = pathlib.Path(path)
        assert path.is_dir()
        assert not Dataset.objects.filter(slug=slug).exists()

        import_dataset(slug, path)
