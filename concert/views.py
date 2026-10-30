import logging
import requests
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import LoginForm, SignUpForm
from .models import Concert, ConcertAttending

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'index.html')


def signup(request):
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('index')
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('index')
    return render(request, 'login.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('index')


def service_resource(request, url, template, key, response_key=None):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        payload = response.json()
        items = payload[response_key] if response_key else payload
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError('Unexpected service response')
    except (requests.RequestException, ValueError, KeyError, TypeError):
        logger.warning('%s service is unavailable', key)
        return render(request, template, {key: [], 'service_error': f'{key.title()} are temporarily unavailable. Please try again later.'}, status=503)
    return render(request, template, {key: items})


def songs(request):
    return service_resource(request, settings.SONGS_URL + '/song', 'songs.html', 'songs', 'songs')


def photos(request):
    return service_resource(request, settings.PICTURES_URL + '/picture', 'photos.html', 'photos')


def concerts(request):
    statuses = dict(ConcertAttending.objects.filter(user=request.user).values_list('concert_id', 'attending')) if request.user.is_authenticated else {}
    rows = [{'concert': concert, 'status': statuses.get(concert.pk, '-')} for concert in Concert.objects.order_by('date', 'id')]
    return render(request, 'concerts.html', {'concerts': rows})


@login_required
def concert_detail(request, id):
    concert = get_object_or_404(Concert, pk=id)
    attending = concert.attendee.filter(user=request.user).first()
    return render(request, 'concert_detail.html', {'concert_details': concert, 'status': attending.attending if attending else '-', 'attending_choices': ConcertAttending.AttendingChoices.choices})


@login_required
@require_POST
def concert_attendee(request):
    try:
        concert_id = int(request.POST.get('concert_id', ''))
    except (TypeError, ValueError):
        return HttpResponseBadRequest('Invalid concert ID')
    concert = get_object_or_404(Concert, pk=concert_id)
    choice = request.POST.get('attendee_choice')
    if choice not in ConcertAttending.AttendingChoices.values:
        return HttpResponseBadRequest('Invalid attendance status')
    if choice == ConcertAttending.AttendingChoices.ATTENDING:
        ConcertAttending.objects.update_or_create(concert=concert, user=request.user, defaults={'attending': choice})
    else:
        ConcertAttending.objects.filter(concert=concert, user=request.user).delete()
    return redirect('concerts')


def health(request):
    return JsonResponse({'status': 'OK'})
