import sys
import pathlib
import logging

from django.core.management.base import BaseCommand

from app.models import import_labels, Dataset

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler(sys.stdout))


class Command(BaseCommand):
    help = "Imports csv files from a directory on disk."

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help="Dataset slug")
        parser.add_argument('path', type=str)

    def handle(self, slug, path, **options):
        path = pathlib.Path(path)
        assert path.is_dir()
        assert Dataset.objects.filter(slug=slug).exists()

        import_labels(Dataset.objects.get(slug=slug), path)
