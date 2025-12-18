import unicodedata
import uuid

from django.contrib.postgres.search import TrigramSimilarity
from django.db import IntegrityError, models, transaction
from django.db.models import FloatField, OuterRef, Q, Subquery, UniqueConstraint, Value
from django.db.models.aggregates import Count
from django.db.models.expressions import Case, RawSQL, When
from django.db.models.functions import Greatest
from django_countries.fields import CountryField
from django_jsonform.models.fields import ArrayField

from users.models import User


class Universidad(models.Model):
    nombre = models.CharField(max_length=200, null=False)
    sigla = models.CharField(max_length=20, blank=False, null=True)
    webpage = models.URLField(null=True)
    pais = CountryField(null=False, blank=False)
    casa_central = models.CharField(max_length=200, blank=True, default=None, null=True)
    foto_escudo = models.FileField(upload_to="universidades/", blank=True)
    foto_banner = models.FileField(upload_to="universidades/", blank=True)
    is_cruch = models.BooleanField(default=False)
    is_manual = models.BooleanField(default=False)

    webpage_academic = ArrayField(
        models.URLField(blank=True, null=True),
        blank=True,
        default=list,
        size=10,
    )

    id_ringgold = models.CharField(max_length=20, blank=True, default=None, null=True, unique=True)
    id_wikidata = models.CharField(max_length=20, blank=True, default=None, null=True, unique=True)
    id_ror = models.CharField(max_length=20, blank=True, default=None, null=True, unique=True)
    id_isni = models.CharField(max_length=20, blank=True, default=None, null=True, unique=True)
    id_crossref = models.CharField(max_length=20, blank=True, default=None, null=True, unique=True)

    # Historial
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "universidades"
        ordering = ["nombre"]
        constraints = [UniqueConstraint(fields=["nombre", "pais"], condition=Q(is_deleted=False), name="unique_nombre_pais_not_deleted")]

    class UniversidadManager(models.Manager):
        class UniversidadQuerySet(models.QuerySet):
            def get_by_name_or_sigla(self, query):
                try:
                    query_normalized = Universidad(nombre=query).get_normalized_name()
                    for universidad in self:
                        if universidad.get_normalized_name() == query_normalized:
                            return universidad
                    if self.sigla:
                        return self.get(sigla__iexact=query.upper().strip())
                    return None
                except Exception:
                    return None

            def get_by_name_or_sigla_fuzzy(self, query, threshold=0.75):
                """
                Perform fuzzy matching (TrigramSimilarity) against several fields
                including arrays (alternative names, acronyms) using SQL subqueries.
                Returns the best-matching object and its similarity score.
                """
                # Subquery for best similarity within openalex_alternative_names
                alt_similarity = Subquery(
                    OpenAlexInsitution.objects.filter(universidad=OuterRef("pk"))
                    .annotate(
                        max_alt_sim=RawSQL(
                            "SELECT MAX(similarity(val, %s)) FROM unnest(openalex_alternative_names) val",
                            (query,),
                        )
                    )
                    .values("max_alt_sim")[:1],
                    output_field=FloatField(),
                )

                # --- Subquery for best similarity within openalex_acronyms ---
                acr_similarity = Subquery(
                    OpenAlexInsitution.objects.filter(universidad=OuterRef("pk"))
                    .annotate(
                        max_acr_sim=RawSQL(
                            "SELECT MAX(similarity(val, %s)) FROM unnest(openalex_acronims) val",
                            (query,),
                        )
                    )
                    .values("max_acr_sim")[:1],
                    output_field=FloatField(),
                )

                qs = self.annotate(
                    sim_nombre=TrigramSimilarity("nombre", query),
                    sim_sigla=TrigramSimilarity("sigla", query),
                    sim_en_name=TrigramSimilarity("openalex_institution__openalex_en_name", query),
                    sim_es_name=TrigramSimilarity("openalex_institution__openalex_es_name", query),
                    sim_alternatives=alt_similarity,
                    sim_acronyms=acr_similarity,
                ).filter(
                    Q(sim_nombre__gt=threshold)
                    | Q(sim_sigla__gt=threshold)
                    | Q(sim_en_name__gt=threshold)
                    | Q(sim_es_name__gt=threshold)
                    | Q(sim_alternatives__gt=threshold)
                    | Q(sim_acronyms__gt=threshold)
                )

                # --- Find best-scoring object ---
                best_obj = None
                best_score = 0

                for obj in qs:
                    sim_fields = {
                        "nombre": obj.sim_nombre,
                        "sigla": obj.sim_sigla,
                        "en_name": obj.sim_en_name,
                        "es_name": obj.sim_es_name,
                        "alternatives": obj.sim_alternatives,
                        "acronyms": obj.sim_acronyms,
                    }
                    sim_fields = {k: v for k, v in sim_fields.items() if v is not None}
                    if sim_fields:
                        field = max(sim_fields, key=sim_fields.get)
                        score = sim_fields[field]
                        if best_obj is None or score > best_score:
                            best_obj = obj
                            best_score = score

                if best_obj:
                    return best_obj, best_score
                return None, None

            def order_by_priority(self, query=None):
                """
                Order universities by priority:
                1. (optional) Trigram similarity on nombre if query provided
                2. OpenAlex type (funder > education > others)
                3. Number of associated academicos (desc)
                4. Number of associated grados (desc)
                """
                qs = self.annotate(
                    openalex_type_rank=Case(
                        When(openalex_institution__openalex_type__iexact="funder", then=Value(3)),
                        When(openalex_institution__openalex_type__iexact="education", then=Value(2)),
                        When(openalex_institution__openalex_type__isnull=False, then=Value(1)),
                        default=Value(0),
                        output_field=models.IntegerField(),
                    ),
                    academicos_count=Count("unidades_set__academico", distinct=True),
                    grados_count=Count("unidades_set__gradoinstancia", distinct=True),
                )
                order_fields = ["-openalex_type_rank", "-academicos_count", "-grados_count"]
                if query:
                    name_cases = [
                        Greatest(
                            TrigramSimilarity("nombre", query_item),
                            Case(
                                When(sigla__iexact=query_item, then=Value(1.0)),
                                default=Value(0.0),
                                output_field=FloatField(),
                            ),
                            output_field=FloatField(),
                        )
                        for query_item in query
                    ]

                    name_cases.append(Value(0))
                    order_fields = ["-similarity"] + order_fields
                    qs = qs.annotate(similarity=Greatest(*name_cases, output_field=models.FloatField()))
                return qs.order_by(*order_fields)

        def get_queryset(self):
            return self.UniversidadQuerySet(self.model, using=self._db)

        def get_by_name_or_sigla(self, query):
            return self.get_queryset().get_by_name_or_sigla(query)

        def get_by_name_or_sigla_fuzzy(self, query):
            return self.get_queryset().get_by_name_or_sigla_fuzzy(query)

    objects = UniversidadManager()

    def save(self, *args, **kwargs):
        """
        Override save to enforce unique normalized check within the same university.
        """
        for universidad in Universidad.objects.filter(pais=self.pais).exclude(id=self.id).exclude(is_deleted=True):
            if universidad.get_normalized_name() == self.get_normalized_name():
                raise IntegrityError(
                    f"A Universidad with the  name '{self.nombre}' already exists {universidad.pk} {universidad.nombre} in {self.pais}."
                )

        super().save(*args, **kwargs)

    def get_or_create_default_unidad(self):
        unidad, created = Unidad.objects.get_or_create(
            universidad=self, nombre="Unidad de Computación", defaults={"sigla": None, "is_default": True}
        )
        return unidad

    def get_normalized_name(self):
        """
        Returns the normalized form of university name, replaces accented characters and special unicode characters and removes
        words with len < 2.Replaces skipwords/tags with common articles
        """
        normalized = unicodedata.normalize("NFD", self.nombre)
        cleaned = "".join(c for c in normalized if not unicodedata.combining(c)).lower().replace("-", " ")
        skipwords = [" de ", " la ", " el ", " y ", " en ", " del ", " los ", " las ", " al ", " a "]
        cleaned = " ".join([word for word in cleaned.split() if word not in skipwords])
        # cleaned=" ".join([word for word in cleaned.split() if len(word)>2])

        for ch in ["\u200b", "\u200c", "\u200d", "\ufeff"]:
            cleaned = cleaned.replace(ch, "")
        return cleaned

    def soft_delete(self):
        with transaction.atomic():
            self.is_deleted = True
            self.save()
            if hasattr(self, "openalex_institution"):
                openalex = self.openalex_institution
                openalex.is_deleted = True
                openalex.save()

    def __str__(self):
        if self.sigla:
            return f"{self.nombre} ({self.sigla})"
        else:
            return str(self.nombre)

    # fetching and  verficiation
    @property
    def is_verification_pending(self):
        """
        True if external data has not been fetched yet (no OpenAlex institution linked)
        """
        return not hasattr(self, "openalex_institution") or self.openalex_institution is None

    @property
    def is_verified(self):
        """
        True if at least one external identifier exists.
        """
        if hasattr(self, "openalex_institution") and self.openalex_institution:
            if self.openalex_institution.openalex_id:
                return True
        if self.id_ror or self.id_ringgold or self.id_wikidata or self.id_isni or self.id_crossref:
            return True
        return False

    @property
    def is_unverified(self):
        """
        True if verification has been attempted but no external identifiers are present.
        """
        # Pending fetch means verification is not attempted yet
        if self.is_verification_pending:
            return False
        # If fetched but no external IDs exist
        if not self.is_verified:
            return True
        return False

    def get_verification_error(self):
        """
        Returns a string describing why the university is unverified.
        """
        if self.is_unverified:
            return "ID_MISSING"
        return None

    @property
    def is_verificado(self):
        return SecretarioInstitucion.objects.filter(institucion=self).count() > 0

    # handy shortcuts
    @property
    def openalex_id(self):
        return self.openalex_institution.openalex_id if hasattr(self, "openalex_institution") else None

    # Deambiguating external data
    @property
    def get_webpage(self):
        if self.webpage:
            return self.webpage
        if getattr(self, "openalex_institution", None):
            return self.openalex_institution.openalex_home_page_url
        return None

    @property
    def get_foto_escudo(self):
        if self.foto_escudo:
            return self.foto_escudo
        if getattr(self, "openalex_institution", None):
            return self.openalex_institution.openalex_thumbnail_url
        return None

    @property
    def get_sigla(self):
        if self.sigla:
            return self.sigla
        if getattr(self, "openalex_institution", None):
            return self.openalex_institution.openalex_acronims[0] if len(self.openalex_institution.openalex_acronims) > 0 else None
        return None

    @property
    def get_alternative_siglas(self):
        siglas = set()
        if self.sigla:
            siglas.add(self.sigla)
        if getattr(self, "openalex_institution", None):
            for s in self.openalex_institution.openalex_acronims:
                if s:
                    siglas.add(s)
        return list(siglas)

    @property
    def get_alternative_names(self):
        names = set()
        names.add(self.nombre)
        if getattr(self, "openalex_institution", None):
            names.update(self.openalex_institution.get_alternative_names())
        return list(names)

    @property
    def get_id_ror(self):
        if self.id_ror:
            return self.id_ror
        if getattr(self, "openalex_institution", None):
            return self.openalex_institution.openalex_id_ror
        return None

    @property
    def get_id_wikidata(self):
        if self.id_wikidata:
            return self.id_wikidata
        if getattr(self, "openalex_institution", None):
            return self.openalex_institution.openalex_id_wikidata
        return None


class OpenAlexInsitution(models.Model):
    # OpenAlex fetched data
    openalex_id = models.CharField(max_length=30, null=False)
    universidad = models.OneToOneField(Universidad, on_delete=models.CASCADE, related_name="openalex_institution", null=False, unique=True)
    openalex_last_fetched_date = models.DateTimeField(auto_now=True, null=True)
    openalex_display_name = models.CharField(max_length=200, blank=True, default=None, null=True)
    openalex_home_page_url = models.CharField(max_length=300, blank=True, default=None, null=True)
    openalex_thumbnail_url = models.CharField(max_length=500, blank=True, default=None, null=True)
    openalex_acronims = ArrayField(
        models.CharField(max_length=50, blank=True, default=None, null=True),
        blank=True,
        default=list,
        size=10,
    )
    openalex_type = models.CharField(max_length=50, blank=True, default=None, null=True)
    openalex_alternative_names = ArrayField(
        models.CharField(max_length=200, blank=True, default=None, null=True),
        blank=True,
        default=list,
        size=50,
    )
    openalex_en_name = models.CharField(max_length=200, blank=True, default=None, null=True)
    openalex_es_name = models.CharField(max_length=200, blank=True, default=None, null=True)
    # external ids
    openalex_id_ror = models.CharField(max_length=20, blank=True, default=None, null=True)
    openalex_id_mag = models.CharField(max_length=20, blank=True, default=None, null=True)
    openalex_id_grid = models.CharField(
        max_length=20,
        blank=True,
        default=None,
        null=True,
    )
    openalex_id_wikipedia = models.CharField(max_length=200, blank=True, default=None, null=True)
    openalex_id_wikidata = models.CharField(max_length=20, blank=True, default=None, null=True)
    # geo data
    openalex_city_name = models.CharField(max_length=100, blank=True, default=None, null=True)
    openalex_city_id = models.CharField(max_length=20, blank=True, default=None, null=True)
    openalex_region_latitude = models.FloatField(blank=True, default=None, null=True)
    openalex_region_longitude = models.FloatField(blank=True, default=None, null=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["openalex_id"], condition=Q(is_deleted=False), name="unique_openalex_id_not_deleted")
        ]

    def get_alternative_names(self):
        names = set(self.openalex_alternative_names or [])
        if self.openalex_display_name:
            names.add(self.openalex_display_name)
        if self.openalex_en_name:
            names.add(self.openalex_en_name)
        if self.openalex_es_name:
            names.add(self.openalex_es_name)
        names.discard(self.universidad.nombre)
        return list(names)


class Unidad(models.Model):
    class Meta:
        verbose_name_plural = "unidades"
        unique_together = (("universidad", "nombre"), ("universidad", "sigla"))

    universidad = models.ForeignKey(Universidad, on_delete=models.PROTECT, related_name="unidades_set")
    nombre = models.CharField(max_length=200, null=False, blank=False)
    sigla = models.CharField(max_length=10, null=True, blank=True)
    webpage = models.URLField(blank=True, null=True)
    foto_escudo = models.FileField(upload_to="universidades/", blank=True, null=True)
    is_manual = models.BooleanField(default=False)

    # Historial
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_default = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        # pylint: disable=E1101
        if self.universidad.nombre and self.nombre:
            return self.universidad.nombre + ":" + self.nombre
        return str(self.nombre) if self.nombre else "(Sin nombre)"


class SecretarioInstitucion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    institucion = models.ForeignKey(Universidad, on_delete=models.CASCADE)


class SecretarioInstitucionInvitacion(models.Model):
    code = models.UUIDField(primary_key=True, default=uuid.uuid4)
    institucion = models.ForeignKey(Universidad, on_delete=models.CASCADE)
    expiration = models.DateTimeField()
    is_confirmed = models.BooleanField(default=False)
