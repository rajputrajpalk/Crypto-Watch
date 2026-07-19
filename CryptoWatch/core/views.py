from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .forms import AlertConfigForm


def dashboard(request: HttpRequest) -> HttpResponse:
    """Render server-side dashboard page (AJAX/Chart data comes from DRF endpoints)."""
    return render(request, 'dashboard.html')


def alert_form_submit(request: HttpRequest) -> HttpResponse:
    """Server-side endpoint for the alert configuration hub."""
    if request.method != 'POST':
        return redirect('dashboard')

    form = AlertConfigForm(request.POST)
    if form.is_valid():
        from .repositories import AlertsRepository

        payload = form.to_payload()
        result = AlertsRepository().create_alert(payload)
        if result.get('status') == 201:
            return redirect('dashboard')

        form.add_error(None, result.get('error', 'Could not create alert'))

    # Re-render dashboard with form errors (no special template context yet).
    return render(request, 'dashboard.html', {'alert_form': form})



