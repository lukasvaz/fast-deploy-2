from django.contrib.auth import login
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.db import transaction, IntegrityError
from users.forms import CustomUserCreationForm
from universidad.models import SecretarioInstitucionInvitacion, SecretarioInstitucion
from persona.models import AcademicoInvitacion


def registro(request, invitation_code):
    if request.method == "GET":
        invitation_obj = get_object_or_404(SecretarioInstitucionInvitacion, code=invitation_code)
        if invitation_obj.is_confirmed:
            return redirect(reverse("front:index"))
        context = {
            "form": CustomUserCreationForm,
            "invitation": invitation_obj,
            "code": invitation_code,
        }
        return render(request, "users_templates/register.html", context)

    elif request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            invitation_obj = get_object_or_404(SecretarioInstitucionInvitacion, code=invitation_code)
            try:
                with transaction.atomic():
                    invitation_obj.is_confirmed = True
                    invitation_obj.save()

                    user = form.save()

                    secretario_institucion_obj = SecretarioInstitucion(
                        user=user,
                        institucion=invitation_obj.institucion,
                    )
                    secretario_institucion_obj.save()

            except IntegrityError:
                return redirect(reverse("front:index"))

            login(request, user)
            return redirect(reverse("front:index"))
        else:
            invitation_obj = get_object_or_404(SecretarioInstitucionInvitacion, code=invitation_code)
            context = {
                "form": form,  # Pass the form with errors
                "invitation": invitation_obj,
                "code": invitation_code,
            }
            return render(request, "users/register.html", context)


def registro_academico(request, invitation_code):
    if request.method == "GET":
        invitation_obj = get_object_or_404(AcademicoInvitacion, code=invitation_code)
        if invitation_obj.is_confirmed:
            return redirect(reverse("front:index"))
        context = {
            "form": CustomUserCreationForm,
            "invitation": invitation_obj,
            "code": invitation_code,
        }
        return render(request, "users_templates/register_academico.html", context)

    elif request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            invitation_obj = get_object_or_404(AcademicoInvitacion, code=invitation_code)
            try:
                with transaction.atomic():
                    invitation_obj.is_confirmed = True
                    invitation_obj.save()

                    user = form.save()

                    academico_obj = invitation_obj.academico
                    academico_obj.user = user
                    academico_obj.save()

            except IntegrityError:
                return redirect(reverse("front:index"))

            login(request, user)
            return redirect(reverse("front:index"))
        else:
            invitation_obj = get_object_or_404(AcademicoInvitacion, code=invitation_code)
            context = {
                "form": form,  # Pass the form with errors
                "invitation": invitation_obj,
                "code": invitation_code,
            }
            return render(request, "users_templates/register_academico.html", context)
