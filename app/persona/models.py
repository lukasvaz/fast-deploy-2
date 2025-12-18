import unicodedata
import uuid

from django.contrib.postgres.search import TrigramSimilarity
from django.db import IntegrityError, models, transaction
from django.db.models import Case, F, JSONField, Sum, Value
from django.db.models.functions import Coalesce, Concat, Greatest
from django_jsonform.models.fields import ArrayField

from grados.models import GradoTipo
from universidad.models import Unidad
from users.models import User


class DblpProfile(models.Model):
    dblp_n_journal = models.IntegerField(default=0)
    dblp_n_conference = models.IntegerField(default=0)
    dblp_id = models.CharField(max_length=200, blank=True, unique=True, null=True)  # unique=True its important
    dblp_affiliation = models.CharField(max_length=200, blank=True, default="")
    dblp_last_publication_date = models.DateField(blank=True, null=True)
    dblp_nombres_externos = ArrayField(
        models.CharField(max_length=200, blank=True),
        blank=True,
        default=list,
        size=5,
    )
    dblp_orcid_id = models.CharField(max_length=200, null=True, blank=True)
    dblp_coauthors = JSONField(blank=True, default=list)

    def reassign_to(self, new_investigador):
        """
        Assign this profile to a new InvestigadorOnDemand.
        Old investigador will have its dblp_profile set to None and all its coauthor relations deleted.
        New investigador will have Coautors relation updated.
        """
        with transaction.atomic():
            if hasattr(self, "investigador_ondemand"):
                old_investigador = self.investigador_ondemand
                old_investigador.dblp_profile = None
                old_investigador.save(update_fields=["dblp_profile"])
                CoautorInvestigador.objects.filter(
                    models.Q(investigador_a=old_investigador) | models.Q(investigador_b=old_investigador)
                ).delete()

            # Ensure the new investigador is saved
            if not new_investigador.pk:  # Check if it has a primary key
                new_investigador.save()  # Save it for the first time

            # Assign the profile to the new investigador
            new_investigador.dblp_profile = self
            new_investigador.save(update_fields=["dblp_profile"])
            CoautorInvestigador.update_investigador_coauthors(new_investigador)


class AminerProfile(models.Model):
    aminer_id = models.CharField(max_length=200, null=True, blank=True, unique=True)
    aminer_webpage = models.URLField(null=True, blank=True)
    aminer_email = models.EmailField(null=True, blank=True)
    aminer_interests = JSONField(blank=True, default=list)

    def reassign_to(self, new_investigador):
        """
        Assign this profile to a new InvestigadorOnDemand.
        Old investigador will have its aminer_profile set to None and all its keyword relations deleted.
        New investigador will be assigned this profile.
        """
        with transaction.atomic():

            if hasattr(self, "investigador_ondemand"):
                old_investigador = self.investigador_ondemand
                old_investigador.aminer_profile = None
                old_investigador.save(update_fields=["aminer_profile"])
                KeywordInvestigador.objects.filter(investigador=old_investigador).delete()

            # Ensure the new investigador is saved
            if not new_investigador.pk:  # Check if it has a primary key
                new_investigador.save()  # Save it for the first time

            # Assign to the new investigador
            new_investigador.aminer_profile = self
            new_investigador.save(update_fields=["aminer_profile"])
            KeywordInvestigador.update_investigador_keywords(new_investigador)


class OpenAlexProfile(models.Model):
    openalex_id = models.CharField(max_length=200, null=True, blank=True, unique=True)
    openalex_id_orcid = models.CharField(max_length=200, null=True, blank=True, unique=True)
    openalex_id_scopus = models.CharField(max_length=200, null=True, blank=True, unique=True)
    openalex_id_wikipedia = models.CharField(max_length=200, null=True, blank=True, unique=True)
    openalex_display_name = models.CharField(max_length=50, null=True, blank=True)
    openalex_display_name_alternative = ArrayField(
        models.CharField(max_length=200, blank=True),
        blank=True,
        default=list,
        size=10,
    )
    openalex_works_counts = models.IntegerField(null=True, blank=True)
    openalex_cited_by_counts = models.IntegerField(null=True, blank=True)
    openalex_last_known_institutions = JSONField(blank=True, default=list)
    openalex_topics = JSONField(blank=True, default=dict)

    def reassign_to(self, new_investigador):
        """
        Assign this profile to a new InvestigadorOnDemand.
        """
        with transaction.atomic():
            if hasattr(self, "investigador_ondemand"):
                old_investigador = self.investigador_ondemand
                old_investigador.openalex_profile = None
                old_investigador.save()

            new_investigador.openalex_profile = self
            new_investigador.save()


class InvestigadorOnDemand(models.Model):
    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200, null=True, blank=True)
    activo = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    manual_orcid = models.CharField(max_length=200, null=True, blank=True)

    dblp_profile = models.OneToOneField(DblpProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="investigador_ondemand")
    aminer_profile = models.OneToOneField(
        AminerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="investigador_ondemand"
    )
    openalex_profile = models.OneToOneField(
        OpenAlexProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="investigador_ondemand"
    )

    class Meta:
        verbose_name_plural = "investigadores on demand"

    def delete(self, using=None, keep_parents=False):
        # delete associated profiles
        if self.dblp_profile:
            self.dblp_profile.delete()
        if self.aminer_profile:
            self.aminer_profile.delete()
        if self.openalex_profile:
            self.openalex_profile.delete()
        # keyword and coauthors will be deleted by cascade
        return super().delete(using, keep_parents)

    def get_full_name_normalized(self):
        """
        Returns the normalized form of full name (nombre + apellido), replaces accented characters and special unicode characters and removes
        words with len < 2.
        Example:
            Hans Löbel -> hans lobel
        """
        if hasattr(self, "academico") and self.academico:
            return self.academico.get_full_name_normalized()
        else:
            full_name = (self.nombre or "").strip()
            if self.apellido:
                full_name += " " + (self.apellido or "").strip()
            normalized = unicodedata.normalize("NFD", full_name)
            cleaned = "".join(c for c in normalized if not unicodedata.combining(c)).lower().replace("-", " ")
            cleaned = " ".join([word for word in cleaned.split() if len(word) > 2])
            for ch in ["\u200b", "\u200c", "\u200d", "\ufeff"]:
                cleaned = cleaned.replace(ch, "")
            return cleaned

    # deambiguating external data
    @property
    def orcid_id(self):
        if self.manual_orcid or self.manual_orcid == "":
            return self.manual_orcid
        if self.dblp_profile and self.dblp_profile.dblp_orcid_id:
            return self.dblp_profile.dblp_orcid_id
        if self.openalex_profile and self.openalex_profile.openalex_id_orcid:
            return self.openalex_profile.openalex_id_orcid
        return None

    @property
    def get_alternative_names(self):
        names = set()
        if self.dblp_profile and hasattr(self.dblp_profile, "dblp_nombres_externos"):
            for n in self.dblp_profile.dblp_nombres_externos:
                if n:
                    names.add(n)
        if self.openalex_profile and hasattr(self.openalex_profile, "openalex_display_name_alternative"):
            for n in self.openalex_profile.openalex_display_name_alternative:
                if n:
                    names.add(n)

        if self.openalex_profile and self.openalex_profile.openalex_display_name:
            names.add(self.openalex_profile.openalex_display_name)

        names.discard(self.academico.get_full_name())
        return list(names)

    # getters for all fields in related profiles (for backward compatibility)
    @property
    def dblp_n_journal(self):
        return self.dblp_profile.dblp_n_journal if self.dblp_profile else None

    @property
    def dblp_n_conference(self):
        return self.dblp_profile.dblp_n_conference if self.dblp_profile else None

    @property
    def dblp_id(self):
        return self.dblp_profile.dblp_id if self.dblp_profile else None

    @property
    def dblp_affiliation(self):
        return self.dblp_profile.dblp_affiliation if self.dblp_profile else None

    @property
    def dblp_last_publication_date(self):
        return self.dblp_profile.dblp_last_publication_date if self.dblp_profile else None

    @property
    def dblp_nombres_externos(self):
        return self.dblp_profile.dblp_nombres_externos if self.dblp_profile else []

    @property
    def aminer_id(self):
        return self.aminer_profile.aminer_id if self.aminer_profile else None

    @property
    def aminer_webpage(self):
        return self.aminer_profile.aminer_webpage if self.aminer_profile else None

    @property
    def aminer_email(self):
        return self.aminer_profile.aminer_email if self.aminer_profile else None

    @property
    def openalex_id(self):
        return self.openalex_profile.openalex_id if self.openalex_profile else None

    @property
    def openalex_id_orcid(self):
        return self.openalex_profile.openalex_id_orcid if self.openalex_profile else None

    @property
    def openalex_id_scopus(self):
        return self.openalex_profile.openalex_id_scopus if self.openalex_profile else None

    @property
    def openalex_id_wikipedia(self):
        return self.openalex_profile.openalex_id_wikipedia if self.openalex_profile else None

    @property
    def openalex_display_name(self):
        return self.openalex_profile.openalex_display_name if self.openalex_profile else None

    @property
    def openalex_display_name_alternative(self):
        return self.openalex_profile.openalex_display_name_alternative if self.openalex_profile else []

    @property
    def openalex_works_counts(self):
        return self.openalex_profile.openalex_works_counts if self.openalex_profile else None

    @property
    def openalex_cited_by_counts(self):
        return self.openalex_profile.openalex_cited_by_counts if self.openalex_profile else None

    @property
    def openalex_last_known_institutions(self):
        return self.openalex_profile.openalex_last_known_institutions if self.openalex_profile else []

    @property
    def openalex_topics(self):
        return self.openalex_profile.openalex_topics if self.openalex_profile else []


class CoautorInvestigador(models.Model):
    investigador_a = models.ForeignKey(
        InvestigadorOnDemand,
        on_delete=models.CASCADE,
        related_name="investigador_a",
    )
    investigador_b = models.ForeignKey(
        InvestigadorOnDemand,
        on_delete=models.CASCADE,
        related_name="investigador_b",
    )
    peso = models.IntegerField()

    @classmethod
    def update_investigador_coauthors(cls, investigador_obj):
        """
        Update coauthors based on the dblpProfile coauthors data.
        """
        # delete old coauthor relations
        with transaction.atomic():
            CoautorInvestigador.objects.filter(
                models.Q(investigador_a=investigador_obj) | models.Q(investigador_b=investigador_obj)
            ).delete()

            # update or create new coauthor relations
            if not investigador_obj.dblp_profile:
                return
            profile_obj = investigador_obj.dblp_profile
            coautor_data_dict = profile_obj.dblp_coauthors or {}
            for coautor_dblp_id, coautor_data in coautor_data_dict.items():
                # Check if investigador exist
                investigador_coautor_obj = InvestigadorOnDemand.objects.none()
                investigador_coautor_query = InvestigadorOnDemand.objects.filter(dblp_profile__dblp_id=coautor_dblp_id)
                if not investigador_coautor_query:
                    investigador_coautor_obj = InvestigadorOnDemand(
                        nombre=coautor_data["nombre"],
                        dblp_profile=DblpProfile.objects.create(dblp_id=coautor_dblp_id),
                    )
                    investigador_coautor_obj.save()
                else:
                    investigador_coautor_obj = investigador_coautor_query[0]

                # Check if coautor relation exist
                coautor_relation_query = CoautorInvestigador.objects.filter(
                    investigador_a=investigador_coautor_obj,
                    investigador_b=investigador_obj,
                )
                coautor_relation_query |= CoautorInvestigador.objects.filter(
                    investigador_b=investigador_coautor_obj,
                    investigador_a=investigador_obj,
                )
                if not coautor_relation_query:
                    coautor_relation_obj = CoautorInvestigador(
                        investigador_a=investigador_obj,
                        investigador_b=investigador_coautor_obj,
                        peso=coautor_data["peso"],
                    )
                    coautor_relation_obj.save()
                else:
                    coautor_relation_obj = coautor_relation_query[0]
                    coautor_relation_obj.peso = coautor_data["peso"]
                    coautor_relation_obj.save()


class InvestigadorCandidato(models.Model):
    buscado = models.CharField(max_length=200, blank=True, unique=True)
    valid = models.BooleanField(default=False)
    candidatos = ArrayField(
        models.CharField(max_length=200, blank=True),
        blank=True,
        default=list,
        size=150,
    )

    # Historial
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)


class Academico(models.Model):
    class Meta:
        unique_together = ("nombre", "apellido", "unidad")

    class AcademicoManager(models.Manager):
        class AcademicoQuerySet(models.QuerySet):
            def order_by_priority(self, names_query=None, keywords=None):
                """
                Orders academics by priority:
                1 query : list of query params to search in nombre + apellido or keyword using trigram similarity
                2. Academics with OpenAlex profile come first
                3. Within those with OpenAlex profile, those with higher openalex_cited_by

                """
                academicos = self.annotate(
                    has_openalex=Case(
                        models.When(investigador_ondemand__openalex_profile__isnull=False, then=models.Value(1)),
                        default=models.Value(0),
                        output_field=models.IntegerField(),
                    ),
                    openalex_cited=models.functions.Coalesce(
                        models.F("investigador_ondemand__openalex_profile__openalex_cited_by_counts"),
                        models.Value(0),
                    ),
                )
                order_clause = ["-has_openalex", "-openalex_cited"]
                # keep  greatest similarity and kw_peso if multiple query items
                if keywords:
                    kw_cases = [
                        models.Subquery(
                            KeywordInvestigador.objects.filter(
                                investigador=models.OuterRef("investigador_ondemand"),
                                keyword__in=keywords,
                            )
                            .annotate(
                                total_peso=Sum("investigador__keywordinvestigador__peso"), normalized_peso=F("peso") * 1.0 / F("total_peso")
                            )
                            .values("normalized_peso")[:1],  # Use normalized_peso
                            output_field=models.FloatField(),
                        )
                    ]
                    kw_cases.append(Value(0))
                    order_clause = ["-kw_peso"] + order_clause
                    academicos = academicos.annotate(kw_peso=Greatest(*kw_cases, output_field=models.FloatField()))

                if names_query:
                    name_cases = [
                        Greatest(
                            TrigramSimilarity(
                                Concat(
                                    Coalesce("nombre", Value("")),
                                    Value(" "),
                                    Coalesce("apellido", Value("")),
                                ),
                                query_item,
                            ),
                            Value(0.2),
                        )
                        for query_item in names_query
                    ]
                    name_cases.append(Value(0))
                    order_clause = ["-similarity"] + order_clause

                    academicos = academicos.annotate(similarity=Greatest(*name_cases, output_field=models.FloatField()))

                return academicos.order_by(*order_clause)

        def get_or_create(self, nombre, apellido=None, unidad=None, **kwargs):
            full_name_norm = Academico(nombre=nombre, apellido=apellido, unidad=unidad).get_full_name_normalized()

            # Search for normalized names
            for academico in self.filter(unidad__universidad=unidad.universidad):
                db_full_name_norm = academico.get_full_name_normalized()
                if set(db_full_name_norm.split()) <= set(full_name_norm.split()) or set(full_name_norm.split()) <= set(
                    db_full_name_norm.split()
                ):
                    return academico, False

            # If not found, create new
            return super().get_or_create(nombre=nombre, apellido=apellido, unidad=unidad, **kwargs)

        def get_queryset(self):
            return self.AcademicoQuerySet(self.model, using=self._db)

    objects = AcademicoManager()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    # foreign keys
    investigador_candidato = models.ForeignKey(InvestigadorCandidato, on_delete=models.SET_NULL, blank=True, null=True)
    investigador_candidato_pos = models.IntegerField(blank=True, null=True)
    investigador_ondemand = models.OneToOneField(
        InvestigadorOnDemand, on_delete=models.SET_NULL, blank=True, null=True, related_name="academico"
    )
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200, null=True, blank=True)
    webpage = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    email_is_public = models.BooleanField(default=True)
    foto = models.FileField(upload_to="uploads/", blank=True)
    grado_maximo = models.CharField(max_length=30, choices=GradoTipo.choices, null=True, blank=True)
    github = models.CharField(max_length=200, blank=True)
    linkedin = models.CharField(max_length=200, blank=True)
    twitter = models.CharField(max_length=200, blank=True)

    # history data
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    openalex_last_fetched_date = models.DateTimeField(null=True, blank=True)
    dblp_last_fetched_date = models.DateTimeField(null=True, blank=True)
    aminer_last_fetched_date = models.DateTimeField(null=True, blank=True)

    is_deleted = models.BooleanField(default=False)

    def get_full_name(self):
        nombre = (self.nombre or "").strip()
        apellido = (self.apellido or "").strip()
        if apellido:
            return f"{nombre} {apellido}".strip()
        return nombre

    def get_full_name_normalized(self):
        """
        Returns the normalized form of full name (nombre + apellido), replaces accented characters and special unicode characters and removes
        words with len < 2.
        Example:
            Hans Löbel -> hans lobel
        """
        normalized = unicodedata.normalize("NFD", self.get_full_name())
        cleaned = "".join(c for c in normalized if not unicodedata.combining(c)).lower().replace("-", " ")
        cleaned = " ".join([word for word in cleaned.split() if len(word) > 2])
        for ch in ["\u200b", "\u200c", "\u200d", "\ufeff"]:
            cleaned = cleaned.replace(ch, "")
        return cleaned

    def save(self, *args, **kwargs):
        """
        Override save to enforce unique normalized full name within the same university.
        """
        full_name_normalized = self.get_full_name_normalized()
        # Check for existing Academico with same normalized full name in university
        for academico in Academico.objects.filter(unidad__universidad=self.unidad.universidad).exclude(id=self.id):
            db_full_name = academico.get_full_name_normalized()
            if db_full_name == full_name_normalized or db_full_name in full_name_normalized or full_name_normalized in db_full_name:
                raise IntegrityError(
                    f"An Academico with the name '{self.get_full_name()}' already exists: {db_full_name} in  {self.unidad}."
                )
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """
        Custom delete method to cascade delete related user and investigador_ondemand.
        """
        with transaction.atomic():
            if self.user:
                self.user.delete()
            if self.investigador_ondemand:
                self.investigador_ondemand.delete()
            if self.investigador_candidato:
                self.investigador_candidato.delete()
            return super().delete(using, keep_parents)

    # fetching and  verficiation
    @property
    def is_verification_pending(self):
        if not self.aminer_last_fetched_date and not self.openalex_last_fetched_date and not self.dblp_last_fetched_date:
            return True
        return False

    @property
    def is_verified(self):
        io = getattr(self, "investigador_ondemand", None)
        if io and not self.is_verification_pending:
            return io.aminer_id is not None or io.openalex_id is not None or io.dblp_id is not None
        return False

    @property
    def is_unverified(self):
        io = getattr(self, "investigador_ondemand", None)
        if not io:
            return True
        if not self.is_verification_pending:
            return io.aminer_id is None and io.openalex_id is None and io.dblp_id is None
        return False

    def get_verification_error(self):
        if self.is_unverified:
            return "ID_MISSING"

    @property
    def universidad(self):
        return self.unidad.universidad if self.unidad else None

    # deambiguate external data
    @property
    def get_webpage(self):
        if not self.webpage:
            if self.investigador_ondemand and self.investigador_ondemand.aminer_webpage:
                return self.investigador_ondemand.aminer_webpage
        else:
            return self.webpage

    @property
    def get_email(self):
        if not self.email:
            if self.investigador_ondemand and self.investigador_ondemand.aminer_email:
                return self.investigador_ondemand.aminer_email
        else:
            return self.email

    def __str__(self):
        return str(self.nombre)


class Dominio(models.Model):
    nombre = models.CharField(max_length=200)

    def __str__(self):
        return str(self.nombre)


class DominioAcademico(models.Model):
    class Meta:
        verbose_name_plural = "dominios academicos"

    academico = models.ForeignKey(Academico, on_delete=models.CASCADE)
    dominio = models.ForeignKey(Dominio, on_delete=models.CASCADE)


class Area(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(max_length=2000, blank=True)

    def __str__(self):
        return str(self.nombre)


class Subarea(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(max_length=2000, blank=True)

    class Meta:
        unique_together = ("area", "nombre")

    def __str__(self):
        return str(self.nombre)


class Keyword(models.Model):
    nombre = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return str(self.nombre)


class AmbitoTrabajo(models.Model):
    class Meta:
        verbose_name_plural = "ambitos de trabajo"

    academico = models.ForeignKey(Academico, on_delete=models.CASCADE)
    subarea = models.ForeignKey(Subarea, on_delete=models.CASCADE)
    peso = models.IntegerField(blank=True, null=True)
    manual = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    @classmethod
    def update_academico_ambitos(cls, academico_ob, is_manual=False):
        """
        Update the AmbitoTrabajo entries for the given Academico based on the data in its InvestigadorOnDemand profiles (OpenAlex-topics and Aminer-interests).Deletes old ambitos
        """
        with transaction.atomic():
            if not getattr(academico_ob, "investigador_ondemand", None):
                return
            io = academico_ob.investigador_ondemand
            # Remove existing AmbitoTrabajo entries not in the new subareas
            cls.objects.filter(academico=academico_ob).delete()

            if getattr(io, "openalex_profile", None) and getattr(io.openalex_profile, "openalex_topics", None):
                merged_topics = io.openalex_profile.openalex_topics
                subarea_qs = Subarea.objects.filter(nombre__in=merged_topics.keys())
                for subarea in subarea_qs:
                    cls.objects.create(academico=academico_ob, subarea=subarea, peso=merged_topics[subarea.nombre], manual=is_manual)
            elif getattr(io, "aminer_profile", None) and getattr(io.aminer_profile, "aminer_interests", None):
                merged_kws = io.aminer_profile.aminer_interests
                keyword_qs = Keyword.objects.filter(nombre__in=merged_kws.keys())
                for keyword in keyword_qs:
                    for sub in keyword.subarea.all():
                        cls.objects.create(academico=academico_ob, subarea=sub, peso=merged_kws[keyword.nombre], manual=is_manual)


class KeywordInvestigador(models.Model):
    class Meta:
        verbose_name_plural = "Keywords investigador"

    investigador = models.ForeignKey(InvestigadorOnDemand, on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE)
    peso = models.IntegerField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    @classmethod
    def update_investigador_keywords(cls, investigador_obj):
        """
        Update keywords based on the aminerProfile interests data.
        """
        with transaction.atomic():
            # delete old keyword relations
            cls.objects.filter(investigador=investigador_obj).delete()
            if not investigador_obj.aminer_profile:
                return
            profile_obj = investigador_obj.aminer_profile
            interests_dict = profile_obj.aminer_interests or {}
            for keyword_name, peso in interests_dict.items():
                # Check if keyword exist
                keyword_obj, created = Keyword.objects.get_or_create(nombre=keyword_name)
                # Create new keyword relation
                keyword_relation_obj = cls(investigador=investigador_obj, keyword=keyword_obj, peso=peso, activo=True)
                keyword_relation_obj.save()


class AcademicoInvitacion(models.Model):
    code = models.UUIDField(primary_key=True, default=uuid.uuid4)
    academico = models.ForeignKey(Academico, on_delete=models.CASCADE)
    expiration = models.DateTimeField()
    is_confirmed = models.BooleanField(default=False)
