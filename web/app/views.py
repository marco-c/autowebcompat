import random
import io
import logging

from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import engines
from PIL import Image, ImageChops
from django.views.decorators.csrf import csrf_protect
import django_tables2

from . import models, tables

log = logging.getLogger(__name__)
LINES_PER_TABLE_PAGE = 7


def render(request, template, context={}):
    context['request'] = request
    return HttpResponse(engines['jinja2'].get_template(template).render(context=context, request=request))


def configure_table(request, table):
    django_tables2.RequestConfig(
        request,
        paginate={'per_page': LINES_PER_TABLE_PAGE},
    ).configure(table)


def table_from_queryset(table_class, query, title):
    table = table_class(query)
    return {
        'title': title,
        'model_name': table.__class__.Meta.model.__name__,
        'table': table,
        'count': query.count(),
    }


def get_detail_view(model_class, get_tables=None, template='app/detail.html'):
    def view(request, **kwargs):
        inst = get_object_or_404(model_class, **kwargs)
        tables = get_tables(inst) if get_tables is not None else []
        for res in tables:
            configure_table(request, res['table'])
        ctx = {
            'title': str(inst),
            'model_name': inst.__class__.__name__,
            'item': inst,
            'tables': tables,
        }
        return render(request, template, ctx)
    return view


def get_table_view(table_class, query):
    def view(request, **kwargs):
        title = f'All {table_class.Meta.model.__name__}s'
        ctx = table_from_queryset(table_class, query, title)
        configure_table(request, ctx['table'])
        return render(request, 'app/table.html', ctx)
    return view


def index(request):
    return render(request, "app/home.html")


def vote(request):
    request.user.label_set
    user_decisions = models.Label.objects.filter(user=request.user)
    query = models.Decision.objects.exclude(id__in=user_decisions)
    cent = list(query.order_by('updated_at')[:100])
    if not cent:
        return HttpResponse('You labeled everything we have. Thanks.')
    return HttpResponseRedirect(random.choice(cent).get_absolute_url())


def ping(request):
    return HttpResponse("pong.")


user_list = get_table_view(
    tables.UserTable,
    User.objects.all(),
)
user = get_detail_view(
    User,
    lambda user: [
        table_from_queryset(tables.LabelTable, user.label_set.all(), 'Labels created by this user'),
    ],
    'app/detail/user.html',
)

dataset_list = get_table_view(
    tables.DatasetTable,
    models.Dataset.objects.all(),
)
dataset = get_detail_view(
    models.Dataset,
    lambda dataset: [
        table_from_queryset(
            tables.SequenceTable,
            dataset.sequence_set.all(),
            'Sequences for this dataset',
        ),
        table_from_queryset(
            tables.ScreenshotTable,
            models.Screenshot.objects.filter(sequence__dataset=dataset).all(),
            'Screenshots taken for this dataset',
        ),
        table_from_queryset(
            tables.DecisionTable,
            models.Decision.objects.filter(pic_left__sequence__dataset=dataset).all(),
            'Decisions created for this dataset',
        ),
    ],
)

sequence_list = get_table_view(
    tables.SequenceTable,
    models.Sequence.objects.all(),
)
sequence = get_detail_view(
    models.Sequence,
    lambda sequence: [
        table_from_queryset(
            tables.ScreenshotTable,
            sequence.screenshot_set.all(),
            'Screenshots',
        ),
        table_from_queryset(
            tables.DecisionTable,
            models.Decision.objects.filter(pic_left__sequence=sequence).all(),
            'Decisions',
        ),
    ],
    'app/detail/sequence.html',
)

screenshot_list = get_table_view(
    tables.ScreenshotTable,
    models.Screenshot.objects.all(),
)
screenshot = get_detail_view(
    models.Screenshot,
    lambda screenshot: [
        table_from_queryset(
            tables.DecisionTable,
            models.Decision.objects.filter(Q(pic_left=screenshot) | Q(pic_right=screenshot)).all(),
            'Decisions for this screenshot'
        ),
    ],
    'app/detail/screenshot.html',
)


@csrf_protect
def submit_label(request):
    assert request.user.is_authenticated
    assert request.method == 'POST'
    decision = models.Decision.objects.get(id=request.POST['decision_id'])
    label = request.POST['label']
    assert label in (c[0] for c in models.Label.LABEL_CHOICES)
    models.set_label(decision.pic_left.sequence.dataset, request.user, decision.key, label)
    return HttpResponseRedirect(decision.get_absolute_url())


decision_list = get_table_view(
    tables.DecisionTable,
    models.Decision.objects.all(),
)
decision = get_detail_view(
    models.Decision,
    lambda decision: [
        table_from_queryset(
            tables.LabelTable,
            decision.label_set.all(),
            'Labels for this decision',
        ),
    ],
    'app/detail/decision.html',
)

network_list = get_table_view(
    tables.NetworkTable,
    models.Network.objects.all(),
)
network = get_detail_view(
    models.Network,
)

network_template_list = get_table_view(
    tables.NetworkTemplateTable,
    models.NetworkTemplate.objects.all(),
)
network_template = get_detail_view(
    models.NetworkTemplate,
)


def png_response(png_bytes):
    resp = HttpResponse(png_bytes, 'image/png')
    resp['Content-Length'] = len(png_bytes)
    resp['Content-Disposition'] = 'inline'
    return resp


def bytes_to_image(png_bytes):
    b = io.BytesIO(png_bytes)
    return Image.open(b).convert(mode='RGB')


def image_to_bytes(image):
    b = io.BytesIO()
    image.save(b, format="png")
    return b.getvalue()


def png_superposition(left_bytes, right_bytes):
    left = bytes_to_image(left_bytes)
    right = bytes_to_image(right_bytes)
    assert left.size == right.size, 'size mismatch'
    assert left.mode == right.mode, f'mode mismatch: {left.mode} {right.mode}'
    result = Image.blend(left, right, 0.5)
    return image_to_bytes(result)


def png_difference(left_bytes, right_bytes):
    left = bytes_to_image(left_bytes)
    right = bytes_to_image(right_bytes)
    result = ImageChops.difference(left, right)
    return image_to_bytes(result)


def img(request, pk):
    log.debug('looking for image %s', pk)
    png = get_object_or_404(models.Screenshot, pk=pk).png.tobytes()
    log.debug('serving img size=%s', len(png))
    assert type(png) == bytes, str(type(png))
    return png_response(png)


def img_superposition(request, pk):
    d = get_object_or_404(models.Decision, pk=pk)
    return png_response(png_superposition(d.pic_left.png.tobytes(), d.pic_right.png.tobytes()))


def img_difference(request, pk):
    d = get_object_or_404(models.Decision, pk=pk)
    return png_response(png_difference(d.pic_left.png.tobytes(), d.pic_right.png.tobytes()))
