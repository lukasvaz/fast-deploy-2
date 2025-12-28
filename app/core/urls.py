from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.urls import re_path
from django.views.static import serve


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="users_templates/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="users_templates/password_change_form.html",
        ),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(template_name="users_templates/password_change_done.html"),
        name="password_change_done",
    ),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(template_name="users_templates/password_reset_form.html"),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="users_templates/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="users_templates/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="users_templates/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("memoria/", include("memoria.urls")),
    path("inst/", include("universidad.urls")),
    path("persona/", include("persona.urls")),
    path("etl/", include("etl.urls")),
    path("api/v1/", include("api.urls")),
    path("users/", include("users.urls")),
    path("", include("front.urls")),
    path("grados/", include("grados.urls")),
    path("revision/", include(("revision.urls", "revision"), namespace="revision")),
    path("subir_archivos/", include(("subir_archivos.urls", "subir_archivos"), namespace="subir_archivos")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]