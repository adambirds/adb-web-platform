"""Keep authenticated analytics and OAuth responses out of shared/browser caches."""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


def analytics_response_headers(
    get_response: Callable[[HttpRequest], HttpResponse],
) -> Callable[[HttpRequest], HttpResponse]:
    def middleware(request: HttpRequest) -> HttpResponse:
        response = get_response(request)
        if request.path.startswith("/api/analytics/"):
            response["Cache-Control"] = "private, no-store"
            response["Referrer-Policy"] = "no-referrer"
        return response

    return middleware
