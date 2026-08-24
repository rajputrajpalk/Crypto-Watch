from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .forms import AlertConfigForm
from .repositories import AlertsRepository


def dashboard(request: HttpRequest) -> HttpResponse:
    """Render main trading dashboard template."""
    return render(request, 'dashboard.html', {
        'form': AlertConfigForm(),
    })


def alert_form_submit(request: HttpRequest) -> HttpResponse:
    """Handle standard POST submission for creating an alert."""
    if request.method != 'POST':
        return redirect('dashboard')

    form = AlertConfigForm(request.POST)
    if form.is_valid():
        payload = form.to_payload()
        result = AlertsRepository().create_alert(payload)
        if result.get('status') == 201:
            return redirect('dashboard')
        form.add_error(None, result.get('error', 'Failed to create alert'))

    return render(request, 'dashboard.html', {'form': form})
