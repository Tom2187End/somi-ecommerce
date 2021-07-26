# Generated by Django 2.2.18 on 2021-07-26 20:51
from django.db import migrations

from shuup.core.catalog import ProductCatalog


def reindex_catalog(apps, schema_editor):
    ShopProduct = apps.get_model("shuup", "ShopProduct")
    from shuup.core.models import ProductMode

    for shop_product in ShopProduct.objects.exclude(product__mode=ProductMode.VARIATION_CHILD):
        ProductCatalog.index_shop_product(shop_product.pk)


class Migration(migrations.Migration):

    dependencies = [
        ("shuup", "0094_product_catalog"),
    ]

    operations = [migrations.RunPython(reindex_catalog, migrations.RunPython.noop)]
