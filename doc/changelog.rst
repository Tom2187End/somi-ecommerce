Shuup Change Log
================

Unreleased
----------

- List all changes after last release here (newer on top).  Each change
  on a separate bullet point line.  Wrap the file at 79 columns or so.
  When releasing next version, the "Unreleased" header will be replaced
  with appropriate version header and this help text will be removed.

Core
~~~~

- Add `can_create_shipment` and `can_create_payment` to `Order`
- Ensure refund amounts are associated with an order line
- Fix tax handling for refunds
- Fix bug: Prevent duplicate categories from all_visible-filter
- Add support for using pricing templatetags for services
- Make refund creation atomic
- Allow refund only for non editable orders
- Create separate refund lines for quantities and amounts
- Fix handling of refunds for discounted lines

Localization
~~~~~~~~~~~~

Admin
~~~~~

- Fix payment and shipment visibility in Orders admin
- Manage category products from category edit view
- Filter products based on category
- Add permission check for dashboard blocks
- Fix required permission issues for various modules
- Make `model_url` context function and add permission check
- Add permission check option to `get_model_url`
- Add permission check to toolbar button classes
- Enable remarkable editor for service description
- Add option to filter product list with manufacturer
- Remove orderability checks from order editor
- Replace buttons with dropdown in Orders admin

Addons
~~~~~~

Front
~~~~~

Xtheme
~~~~~~

Classic Gray Theme
~~~~~~~~~~~~~~~~~~

- Honor customer group pricing options for services
- Enable markdown for service description

Simple Supplier
~~~~~~~~~~~~~~~

Order Printouts
~~~~~~~~~~~~~~~

Campaigns
~~~~~~~~~

- Enable exact quantity matches for products in basket campaigns

Customer Group Pricing
~~~~~~~~~~~~~~~~~~~~~~

Discount Pricing
~~~~~~~~~~~~~~~~

Simple CMS
~~~~~~~~~~

Default Tax
~~~~~~~~~~~

Guide
~~~~~

- Fix admin search for invalid API URL settings

General/miscellaneous
~~~~~~~~~~~~~~~~~~~~~


Shuup 0.4.0
-----------

Released on 2016-06-30 06:00 +0300.

The first Shuup release.

Content of Shuup 0.4.0 is same as :doc:`Shoop 4.0.0 <shoop-changelog>`
with all "shoop" texts replaced with "shuup".
