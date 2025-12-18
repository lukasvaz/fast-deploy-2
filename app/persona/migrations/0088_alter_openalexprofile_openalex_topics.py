from django.db import migrations, models


def set_openalex_topics_not_null(apps, schema_editor):
    print("Setting OpenAlexProfile.openalex_topics null values to empty dict...")
    OpenAlexProfile = apps.get_model("persona", "OpenAlexProfile")
    OpenAlexProfile.objects.filter(openalex_topics__isnull=True).update(openalex_topics="{}")


def convert_array_to_jsonb(apps, schema_editor):
    """
    Safely convert varchar[] to jsonb using PostgreSQL's to_jsonb().
    """
    schema_editor.execute(
        """
        ALTER TABLE persona_openalexprofile
        ALTER COLUMN openalex_topics TYPE jsonb
        USING to_jsonb(openalex_topics);
    """
    )


class Migration(migrations.Migration):

    dependencies = [
        ("persona", "0087_alter_openalexprofile_openalex_topics"),
    ]

    operations = [
        migrations.RunPython(set_openalex_topics_not_null),
        migrations.RunPython(convert_array_to_jsonb),
        migrations.AlterField(
            model_name="openalexprofile",
            name="openalex_topics",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
