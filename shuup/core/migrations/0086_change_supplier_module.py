# Generated by Django 2.2.18 on 2021-05-06 14:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shuup', '0085_longer_order_line_sku'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupplierModule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module_identifier', models.CharField(help_text='Select the types of products this supplier can handle.Example for normal products select just Simple Supplier.', max_length=64, unique=True, verbose_name='module identifier')),
                ('name', models.CharField(help_text='Supplier modules name.', max_length=64, verbose_name='Module name')),
            ],
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='module_identifier',
        ),
        migrations.AddField(
            model_name='product',
            name='internal_type',
            field=models.IntegerField(choices=[(0, 'Product')], default=0),
        ),
        migrations.AddField(
            model_name='supplier',
            name='supplier_modules',
            field=models.ManyToManyField(blank=True, help_text='Select the supplier module to use for this supplier. Supplier modules define the rules by which inventory is managed.', related_name='suppliers', to='shuup.SupplierModule', verbose_name='supplier modules'),
        ),
    ]
