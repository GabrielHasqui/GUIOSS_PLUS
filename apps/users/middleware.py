from django.shortcuts import redirect
from django.urls import resolve, Resolver404


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_url_names = {
            "force_password_change",
            "initial_password_setup",
            "logout",
        }

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = getattr(request.user, "profile", None)

            if profile and profile.must_change_password:
                try:
                    match = resolve(request.path_info)
                    url_name = match.url_name
                except Resolver404:
                    url_name = None

                if url_name not in self.allowed_url_names and not request.path_info.startswith("/static/"):
                    return redirect("force_password_change")

        return self.get_response(request)
