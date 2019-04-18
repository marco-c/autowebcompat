import csv
import json
import logging
import os

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import transaction, models
from django.db.models import CASCADE
from django.urls import reverse

from .apps import AppConfig

app_name = AppConfig.name
log = logging.getLogger(__name__)

STR_LEN = 256
SLUG_LEN = 128
URL_LEN = 4096


class Model(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Dataset(Model):
    name = models.CharField(max_length=STR_LEN)
    slug = models.CharField(max_length=SLUG_LEN, unique=True)

    def __str__(self):
        return f"Dataset {self.id} ({self.slug})"

    def decision_count(self):
        return Decision.objects.filter(pic_left__sequence__dataset=self).count()

    def get_absolute_url(self):
        return reverse('app:dataset', args=[self.slug], current_app=app_name)


class Sequence(Model):
    dataset = models.ForeignKey(Dataset, on_delete=CASCADE)
    url = models.CharField(max_length=URL_LEN, blank=True, default='')
    definition = JSONField()
    original_id = models.IntegerField(null=True, default=None)

    def __str__(self):
        return f"Sequence {self.id} (for {self.dataset.slug})"

    def get_absolute_url(self):
        return reverse('app:sequence', args=[str(self.id)], current_app=app_name)


class Screenshot(Model):
    MAX_PNG_SIZE = 8 * 1024 * 1024

    png = models.BinaryField(max_length=MAX_PNG_SIZE)
    sequence = models.ForeignKey(Sequence, on_delete=CASCADE)
    filename = models.CharField(max_length=STR_LEN)
    browser_name = models.CharField(max_length=SLUG_LEN)
    browser_info = JSONField(default=dict)

    def get_absolute_url(self):
        return reverse('app:screenshot', args=[str(self.id)])

    def get_image_url(self):
        return reverse('app:img', args=[str(self.id)])

    class Meta:
        unique_together = ['sequence', 'filename', 'browser_name']

    def __str__(self):
        return f"Screenshot {self.id} on {self.browser_name} (for {self.sequence.dataset.slug})"


class Decision(Model):
    key = models.CharField(max_length=STR_LEN)
    pic_left = models.ForeignKey(Screenshot, on_delete=CASCADE, related_name='decisions_left')
    pic_right = models.ForeignKey(Screenshot, on_delete=CASCADE, related_name='decisions_right')

    def __str__(self):
        return f"Decision {self.id} (for {self.pic_left.sequence.dataset.slug})"

    def get_absolute_url(self):
        return reverse('app:decision', args=[self.id], current_app=app_name)

    def get_superposition_url(self):
        return reverse('app:img_superposition', args=[self.id], current_app=app_name)

    def get_difference_url(self):
        return reverse('app:img_difference', args=[self.id], current_app=app_name)


class Label(Model):
    LABEL_CHOICES = (
        ('y', 'compatible (y)'),
        ('n', 'not compatible (n)'),
        ('d', 'content differences (d)'),
    )

    user = models.ForeignKey(User, on_delete=CASCADE)
    decision = models.ForeignKey(Decision, on_delete=CASCADE)
    label = models.CharField(max_length=1, choices=LABEL_CHOICES)

    class Meta:
        unique_together = ['decision', 'user']

    def __str__(self):
        return f"Label {self.id} by {self.user.username}: {self.label}"


class NetworkTemplate(Model):
    NETWORKS = ['vgg16', 'vgg19', 'inception', 'vgglike', 'simnet', 'simnetlike', 'resnet50']
    NETWORK_CHOICES = tuple(zip(NETWORKS, NETWORKS))
    OPTIMIZER_CHOICES = (
        ('sgd', 'Stochastic Gradient Descent (sgd)'),
        ('adam', 'Adam (adam)'),
        ('nadam', 'Nesterov Adam (nadam)'),
        ('rms', 'RMSProp (rms)'),
    )
    CLASSIFICATION_TYPE_CHOICES = (
        ('Y vs D + N', 'detect content differences as errors (y vs d + n)'),
        ('Y + D vs N', 'ignore content differences (y + d vs n)'),
    )

    network_model = models.CharField(
        max_length=STR_LEN,
        choices=NETWORK_CHOICES,
        default=NETWORK_CHOICES[0][0]
    )
    optimizer = models.CharField(
        max_length=STR_LEN,
        choices=OPTIMIZER_CHOICES,
        default=OPTIMIZER_CHOICES[0][0]
    )
    classification_type = models.CharField(
        max_length=STR_LEN,
        choices=CLASSIFICATION_TYPE_CHOICES,
        default=CLASSIFICATION_TYPE_CHOICES[0][0]
    )
    early_stopping = models.BooleanField(default=True)

    def __str__(self):
        return f"NetworkTemplate {self.id} ({self.network_model}, {self.classification_type})"

    def get_absolute_url(self):
        return reverse('app:network_template', args=[self.id], current_app=app_name)


class Network(Model):
    dataset = models.ForeignKey(Dataset, on_delete=CASCADE)
    template = models.ForeignKey(NetworkTemplate, on_delete=CASCADE)
    training_started_at = models.DateTimeField()
    training_ended_at = models.DateTimeField(null=True)
    results = JSONField(null=True)

    def __str__(self):
        return f"Network {self.id} ({self.template.network_model}, {self.template.classification_type})"

    def get_absolute_url(self):
        return reverse('app:network', args=[self.id], current_app=app_name)


class Prediction(Model):
    network = models.ForeignKey(Network, on_delete=CASCADE)
    decision = models.ForeignKey(Decision, on_delete=CASCADE)
    label = models.CharField(max_length=1)


def get_image_pairs(data_dir='data/'):
    data = {
        'firefox': [],
        'chrome': [],
    }

    for file_name in [f for f in os.listdir(data_dir) if f.endswith('.png')]:
        assert 'firefox.png' in file_name or 'chrome.png' in file_name

        browser = 'firefox' if 'firefox.png' in file_name else 'chrome'

        data[browser].append(file_name[:file_name.index('_' + browser + '.png')])

    chrome_images = set(data['chrome'])
    return [image for image in data['firefox'] if image in chrome_images]


def add_screenshots(root, seq, pair):
    screenshots = {}
    for browser in ['chrome', 'firefox']:
        path1 = root / (pair + '_' + browser + '.png')
        with path1.open('rb') as f:
            png = f.read()
        screenshot = Screenshot(png=png, sequence=seq, filename=path1.name, browser_name=browser)
        screenshot.save()
        screenshots[browser] = screenshot
    Decision(key=pair, pic_left=screenshots['firefox'], pic_right=screenshots['chrome']).save()


@transaction.atomic
def import_dataset(slug, root):
    ds = Dataset(name=slug, slug=slug)
    log.info('saving dataset with slug = %s', slug)
    ds.save()

    image_pairs = sorted(get_image_pairs(str(root)))
    log.info('loaded %d image pairs', len(image_pairs))
    multi = set()
    for pair in image_pairs:
        desc_path = root / (pair + '.txt')
        if desc_path.exists():
            with desc_path.open('r') as f:
                log.debug('saving sequence %s', str(desc_path))
                definition = [json.loads(line) for line in f.readlines()]
            seq = Sequence(dataset=ds, definition=definition)
            seq.save()
            for inner_pair in sorted(p for p in image_pairs if p.startswith(pair + '_')):
                multi.add(inner_pair)
                add_screenshots(root, seq, inner_pair)

    for pair in image_pairs:
        if pair in multi:
            continue
        log.warning('saving image pair %s with no definition', pair)
        seq = Sequence(dataset=ds, definition=dict())
        seq.save()
        add_screenshots(root, seq, pair)

    log.info('dataset import done')


def set_label(dataset, user, key, new_label):
    q = Decision.objects.filter(pic_left__sequence__dataset=dataset, key=key)
    if not q.exists():
        log.warn('image pair "%s" not found in dataset "%s"', key, dataset.slug)
        return
    label, _ = Label.objects.get_or_create(decision=q.get(), user=user)
    label.label = new_label
    label.save()


@transaction.atomic
def import_labels(dataset, root):
    for item in root.iterdir():
        if item.is_file() and item.suffix == '.csv':
            log.info('reading %s', str(item))

            username = item.stem
            user, created = User.objects.get_or_create(username=username)
            if created:
                log.info('created user %s', username)
                user.first_name = username
                user.save()
            else:
                log.info('already have user %s', username)

            with item.open('r', newline='') as f:
                reader = csv.DictReader(f)
                total = len(list(reader))
                for i, row in enumerate(reader):
                    if i % 100 == 0:
                        log.debug(f'writing label #{i}/{total} for user {user.get_username()}')
                    set_label(dataset, user, row['Image Name'], row['Label'])
    log.info('label import done')
