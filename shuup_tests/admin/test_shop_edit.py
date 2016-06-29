import pytest
from django.conf import settings
from django.utils.translation import activate

from shuup.admin.modules.shops.views.edit import ShopBaseForm
from shuup.core.models import Shop, ShopStatus
from shuup.testing.factories import (
    create_product, create_random_order, create_random_person,
    get_default_supplier
)
from shuup_tests.utils import printable_gibberish
from shuup_tests.utils.forms import get_form_data


@pytest.mark.django_db
def test_protected_fields():
    activate("en")
    shop = Shop.objects.create(
        name="testshop",
        identifier="testshop",
        status=ShopStatus.ENABLED,
        public_name="test shop",
        domain="derp",
        currency="EUR"
    )
    assert shop.name == "testshop"
    assert shop.currency == "EUR"
    shop_form = ShopBaseForm(instance=shop, languages=settings.LANGUAGES)
    assert not shop_form._get_protected_fields()  # No protected fields just yet, right?
    data = get_form_data(shop_form, prepared=True)
    shop_form = ShopBaseForm(data=data, instance=shop, languages=settings.LANGUAGES)
    _test_cleanliness(shop_form)
    shop_form.save()

    # Now let's make it protected!
    create_product(printable_gibberish(), shop=shop, supplier=get_default_supplier())
    order = create_random_order(customer=create_random_person(), shop=shop)
    assert order.shop == shop

    # And try again...
    data["currency"] = "XBT"  # Bitcoins!
    shop_form = ShopBaseForm(data=data, instance=shop, languages=settings.LANGUAGES)
    assert shop_form._get_protected_fields()  # So protected!
    _test_cleanliness(shop_form)
    shop = shop_form.save()
    assert shop.currency == "EUR"  # But the shop form ignored the change . . .


def _test_cleanliness(shop_form):
    shop_form.full_clean()
    assert not shop_form.errors
    assert shop_form.cleaned_data
