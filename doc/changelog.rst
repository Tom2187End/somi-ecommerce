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

- Add parameter to `PriceDisplayFilter` to specify tax display mode
- Add soft deletion of categories
- Add support to sell products after stock is zero
- Fix refunds for discount lines
- Fix restocking issue when refunding unshipped products
- Make payments for `CustomPaymentProcessor` not paid by default
- Fix shipping status for orders with refunds
- Fix bug in order total price rounding
- Fix bug with duplicates in `Product.objects.list_visible()`
- Fix restocking issues with refunded products
- Add separate order line types for quantity and amount refunds
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

- Trim search criteria when using select2 inputs
- Fix bug in permission change form error message
- Limit change permissions only for superusers
- Add warning to order creator when creating duplicate contacts
- Show discounted unit price on order confirmation page
- Add order address validation to admin order creator
- Fix bug when editing anonymous orders
- Show order line discount percentage in order detail and creator views
- Allow superadmins to login as customer
- Show orderability errors in package product management
- Show stocks in package product management
- Add link to order line product detail page in order editor
- Add product line quick add to order creator
- Add product barcode field to searchable select2 fields
- Filter out deleted products from Stock Management list view
- Show newest contacts and users first in admin list views
- Show list of shipments in order view
- Fix customer, creator, and ordered by links on order detail page
- Prevent picotable from reloading after every change
- Add ability to copy category visibility settings to products
- Reorganize main menu
- Show customer comment on order detail page
- Redirect to order detail page on order submission
- Make contact views extendable
- Make generic Section object for detail view sections
- Display shipment form errors as messages
- Populate tax number from contact for admin order creator
- Move various dashboard blocks to own admin modules
- Prevent shipments from being created for refunded products
- Add `StockAdjustmentType` Enum
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

- Add ability for customers to save their cart
- Ensure email is not blank prior to sending password recovery email
- Send notify event from company created
- Send notify event from user registration
- Fix bug in cart list view with empty taxful total price
- Fix single page checkout for customers not associated with a company
- Use contact default addresses for company creation
- Use home country by default in customer information addresses

Xtheme
~~~~~~

Classic Gray Theme
~~~~~~~~~~~~~~~~~~

- Enable copy between customer information addresses
- Honor customer group pricing options for services
- Enable markdown for service description

Simple Supplier
~~~~~~~~~~~~~~~

- Skip refund lines when getting product stock counts

Order Printouts
~~~~~~~~~~~~~~~

Campaigns
~~~~~~~~~

- Fix bug with campaign discount amounts
- Add category products basket condition and line effect
- Enable exact quantity matches for products in basket campaigns

Customer Group Pricing
~~~~~~~~~~~~~~~~~~~~~~

- Re-style contactgroup pricing admin form

Discount Pricing
~~~~~~~~~~~~~~~~

Simple CMS
~~~~~~~~~~

- Show error when attempting to make a page a child of itself
- Fix plugin links

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
