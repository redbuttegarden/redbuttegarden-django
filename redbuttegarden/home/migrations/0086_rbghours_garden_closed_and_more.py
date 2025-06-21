from django.db import migrations, models
import wagtail.fields


def copy_messages(apps, schema_editor):
    """
    Copy the content of additional_message and additional_emphatic_mesg to their temporary fields.
    """
    RBGHours = apps.get_model('home', 'RBGHours')
    for obj in RBGHours.objects.all():
        obj.additional_message_temp = obj.additional_message
        obj.additional_emphatic_mesg_temp = obj.additional_emphatic_mesg
        obj.save()


class Migration(migrations.Migration):
    dependencies = [
        ('home', '0085_remove_homepage_hours_homepage_hours_section_text_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rbghours',
            name='additional_message_temp',
            field=wagtail.fields.RichTextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rbghours',
            name='additional_emphatic_mesg_temp',
            field=wagtail.fields.RichTextField(blank=True, null=True),
        ),
        migrations.RunPython(copy_messages),
        migrations.RemoveField(
            model_name='rbghours',
            name='additional_message',
        ),
        migrations.RemoveField(
            model_name='rbghours',
            name='additional_emphatic_mesg',
        ),
        migrations.AddField(
            model_name='rbghours',
            name='garden_closed',
            field=models.BooleanField(default=False, help_text='Check this box if the garden is closed for the day'),
        ),
        migrations.RenameField(
            model_name='rbghours',
            old_name='additional_message_temp',
            new_name='additional_message',
        ),
        migrations.RenameField(
            model_name='rbghours',
            old_name='additional_emphatic_mesg_temp',
            new_name='additional_emphatic_mesg',
        ),
    ]
