# Generated by Django 2.2.17 on 2021-01-22 13:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0080_unify_tax_number_max_length'),
        ('shuup_front', '0002_stored_basket_model_name_translatable'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='storedbasket',
            options={'ordering': ('-updated_on',), 'verbose_name': 'stored basket', 'verbose_name_plural': 'stored baskets'},
        ),
        migrations.AddField(
            model_name='storedbasket',
            name='class_spec',
            field=models.CharField(blank=True, max_length=256, verbose_name='class spec'),
        ),
        migrations.AddField(
            model_name='storedbasket',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shuup.Supplier', verbose_name='supplier'),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='baskets_created', to=settings.AUTH_USER_MODEL, verbose_name='creator'),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customer_baskets', to='shuup.Contact', verbose_name='customer'),
        ),
        migrations.AlterField(
            model_name='storedbasket',
            name='orderer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orderer_baskets', to='shuup.PersonContact', verbose_name='orderer'),
        ),
    ]
