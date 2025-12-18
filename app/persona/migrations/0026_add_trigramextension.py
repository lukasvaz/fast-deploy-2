from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("persona", "0025_alter_investigadorcandidato_candidatos_and_more"),
    ]

    operations = [
        TrigramExtension(),
    ]
