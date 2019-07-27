#!/usr/bin/env python

import logging
import pathlib

import click

from autowebcompat.jobs import run_import, run_scrape, run_services

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

log = logging.getLogger(__name__)


@click.group()
def main():
    pass


@main.command()
def services():
    log.info('Launching services')
    run_services()


@main.command('import')
@click.argument('slug', type=str)
@click.argument('path', type=click.Path(exists=True))
def import_dataset(slug, path):
    """Imports a new dataset with its slug and name set to SLUG.
    The files are read from the given PATH."""

    assert slug == slug.lower()
    path = str(pathlib.Path(path).resolve())

    log.info("Launching import job")
    run_import(slug=slug, path=path)


@main.command()
@click.argument('path', type=click.Path())
def scrape(path):
    """Scrapes a dataset and saves it on disk on the given PATH."""

    path = pathlib.Path(path).resolve()
    path.mkdir(exist_ok=True)
    path = str(path)

    log.info("Launching scrape job")
    run_scrape(path)


if __name__ == "__main__":
    main()
