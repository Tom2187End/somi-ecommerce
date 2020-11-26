# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

List all changes after the last release here (newer on top). Each change on a separate bullet point line

## [2.2.9] - 2020-11-23

### Changed

- Core: Increase field lengths in *LogEntry models
  - Add an index to the indentifier for faster querying.
  - Use the same error prevention measures for message than is done for
    identifier in _add_log_entry() for consistency.

### Fixed

- Core: Fix `ProtectedError` when deleting a `Manufacturer` which was still
  connected to product(s).


## [2.2.8] - 2020-11-23

### Added

- Add font size 16 to summernote text editor

### Fixed

- GDPR: make sure to return a blank list in the `get_active_consent_pages`
  method when there is no page to consent


## [2.2.7] - 2020-11-20

### Fixed

- Admin: do not add/remove shop staff member while saving a staff user


## [2.2.6] - 2020-11-17

### Added

- Include products belonging to child categories of filtered category

### Changed

Admin: do not allow non-superusers manage superusers
  - Do not show is_superuser field for non-superusers no matter
    who they are editing
  - Do not show superuser column in list since the superusers are
    already filtered out from non-superusers who are main people
    using the admin panel.


## [2.2.5] - 2020-11-12

### Fixed

- Front: force recalculate lines after setting the payment and shipping methods to the basket in checkout phase

### Changed

- Don't display taxless price when it's equal to taxful in checkout

### Added

- SimpleCMS: Add field to limit a page availability by permission group

## [2.2.4] - 2020-11-09

### Fixed

- Core: Fix basket implementation that was using the same memory
object for all baskets instances in the same process

## [2.2.3] - 2020-11-05

### Fixed

- Add missing id field to the media forms


## [2.2.2] - 2020-11-03

### Fixed

- Prevent duplicate images in product media form
- Do not render duplicate hidden media form field


## [2.2.1] - 2020-11-02

### Changed

- Update French, Finnish and Swedish translations
- Change the Supplier.objects.enabled() filter to only return approved suppliers

### Changed

- Admin: Show a loader in place of picotable when a request is pending.

## [2.2.0] - 2020-10-23

### Possible breaking change

- When updating to this double check your project filters around supplier are working
  after this Supplire shop->shops change.

### Changed

- Admin: change the supplier views to update the approved flag for the current shop only
- Core: change the Supplier object manager to consider the approved flag for the given shop

### Added

- Core: add new module SupplierShop to store thre M2M relationship between the supplier
and the shop with additional attributes

## [2.1.12] - 2020-10-21

### Fixed

- Importer: fix the product importer to prevent parent sku being the current product or other variation child

## [2.1.11] - 2020-10-15

### Added

- Add Spanish and French (CA) translations from Transifex
- Notify: Add a new `attributes` attribute to `shuup.notify.base.Variable` for showing examples
  of which attributes can be accessed in the script templates.
- Notfiy: Show some `Order` related attributes in the notify templates.

### Fixed

- Core: include arbitrary refunds for max refundable amount
- Admin: select product variation in popup window
- Importer: ignore None columns while importing files
- Admin: Show more descriptive error messages in the media uploader in some situations.

### Changed

- Update Finnish and Swedish translations from Transifex
- Importer: add option to import product variations
  - Add option to import product variations
  - Improve handle stock to get supplier by supplier name and
    set the supplier stock managed and update the module identifier.
  - Improve handle stock to set the logical count to desired quantity
    instead adding new stock for the amount. This should help sellers
    to keep their product stock value correct.
- Preserve newlines in vendor and product descriptions even when
 `SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION` and `SHUUP_ADMIN_ALLOW_HTML_IN_VENDOR_DESCRIPTION` are `False`.
- Importer: log errors in the importer and use specific exception classes instead of using Exception
- Notify: make the default script language be the fallback from Parler
- Admin: Hide the 'Root' folder from users that do not have the `"media.view-all"` permission.


## [2.1.10] - 2020-09-29

### Fixed

- Front: fix typo in pagination

### Translations

- Update Finnish and Swedish translations


## [2.1.9] - 2020-09-23

### Fixed

- Fix button that removes coupon from the basket by using the correct JS event property

## [2.1.8] - 2020-09-15

- Update translations strings
- Importer: fix product CSV importer to better match the headers


## [2.1.7] - 2020-09-11

- Admin: improve product variation management. This release purely
  amends release 2.1.6.


## [2.1.6] - 2020-09-11

Admin: add supplier check to product list and edit views
Admin: improve product variation management

  Remove activate template form field as confusing.

  1. Now when add new template:
    - New empty template is created

  2. When you have template selected:
    - Product variations are saved based on the form
    - Variation options are updated to the selected template

  3. When template is not selected:
    - Product variations are saved based on the form


## [2.1.5] - 2020-09-08

### Fixed

- Requirements: require Markdown>=3,<4 instead <3
- Xtheme: Fix social media plugin form initial data population.


## [2.1.4] - 2020-09-08

### Fixed

- Xtheme: fix social media plugin form populate
- GDPR: Fix anonymization error when an order of a contact had no shipping or billing address.


## [2.1.3] - 2020-08-28

### Fixed

- Xtheme: fix model choice widget for plugins (django 2)


## [2.1.2] - 2020-08-26

### Fixed

- Xtheme: fix editor template issue
- Simple CMS: make sure to pass optional parameters through kwargs in form


## [2.1.1] - 2020-08-26

### Added

- Admin: add option to delete attributes

### Fixed

- Xtheme: fix editor template issue and make sure to pass optional parameters through kwargs in form
- Notify: unescape email subject and body to prevent sending broken characters in emails


## [2.1.0] - 2020-08-24

### Added

- shuup.notify: add notification_email_before_send signal to SendMail
- shuup.notify: add event identifier to Context


## [2.0.8] - 2020-08-24

### Fixed

- Prevent crashing when trying to cache an unpicklable value.


## [2.0.7] - 2020-08-21

### Fixed

- Fix passing a `reverse_lazy()` URL as the `upload_url` argument for `FileDnDUploaderWidget`.


## [2.0.6] - 2020-08-18

### Changed

- Admin: Make the order editor keep the suppliers of non-product order lines intact.

### Fixed:

- Admin: Fix the edit button on the order editor.


## [2.0.5] - 2020-08-16

### Added

- Admin: user and permission based access to media folders

  This means that all vendors can have their own root folder and do what every they want in that folder.
  But it also allows the admin to give viewing access to one folder for all suppliers.


## [2.0.4] - 2020-08-07

- Testing: add missing migrations


## [2.0.3] - 2020-08-07

- CMS: add missing migrations


## [2.0.2] - 2020-08-07

### Changed

- Removed Django 1.11 compatible code from the code base

### Fixed

- Admin: fix logout view that was loading the template from Django instead of custom template
- Admin: return `None` when the order source was not correctly initialized in JsonOrderCreator
- Core: add parameter in shuup_static to load the version of a given package


## [2.0.1] - 2020-08-04

- Add initial support for Django 2.2


## [1.11.10] - 2020-08-04

- Fix issue on arranging menu after reset which sets the configuration None
  which in the other hand is hard to update as it is not dict.


## [1.11.9] - 2020-08-04

- Admin: add option to arrange menu for superuses, staff and suppliers

  For now it was only possible to arrange menu per user which is not
  sufficient while the menu needs to be arranged for the whole group
  of people like shop staff or vendors.

  Allow to create menu custom menu for superusers, staff or suppliers,
  but remain the possibility to still arrange the menu per user.

  Add option to translate each menu arranged for these groups since
  not all vendors/suppliers necessary speak same language.


## [1.11.8] - 2020-07-31

### Fixed

- Fix admin order edit tool to use correct id for supplier query
- Admin: limit the Manufacturer delete queryset per shop

### Added

- Notify: added email template object to store reusable email templates for SendEmail actions
  This contains a migration step to move all old body template field to use email templates.

### Changed

- Xtheme: move CodeMirror JS lib dependence to Admin
- Sanitize product description on save if `SHUUP_ADMIN_ALLOW_HTML_IN_PRODUCT_DESCRIPTION` is set to `False`

## [1.11.7] - 2020-07-23

### Added

- Core: Add dynamic measurement unit system
  - New settings for specifying units:
    - `SHUUP_MASS_UNIT`
    - `SHUUP_LENGTH_UNIT`
  - New function for getting the volume unit: `shuup.core.utils.units.get_shuup_volume_unit`

### Changed

- **BREAKING**: Change `Shipment` default weight unit from `kg` to `g`
- **BREAKING**: Change `Shipment` default volume unit from `m3` to `mm3`
- **BREAKING**: Change `ShipmentProduct` default volume unit from `m3` to `mm3`

### Removed

- Remove 'known unit' validation from `MeasurementField`, it can contain any units now

## [1.11.6] - 2020-07-22

### Changed

- Front: Add priority attribute to base order form to enable using precedence

## [1.11.5] - 2020-07-07

### Added

- Add signal when an email is sent by a notification

## [1.11.4] - 2020-07-06

- Fix issue with browser tests

## [1.11.3] - 2020-07-04

### Added

- Add `Dockerfile-dev` for development
- Add Docker instructions to docs

### Changed

- Add theme for the shop in `shuup_init`
- Make the shop not be in maintenance mode in `shuup_init`
- Make `Dockerfile` use `shuup` from PyPi for faster build time

## [1.11.2] - 2020-07-03

- Move workbench sqlite database location for upcoming Docker setup

## [1.11.1] - 2020-07-03

### Added

- Admin: Add settings for controlling allowing HTML in product and vendor descriptions


## [1.11.0] - 2020-07-02

### Changed

- Importer: add context object while initializing a importer class
- Core: use UUID in basket IDs to prevent possible duplicates
- Core: save basket shipping and billing address as dictionary when id is not available
- Front: remove the custom _load() implementation from the basket as it is the same as the core
- Core: ignore lines that are not from the given source while calculating taxes
- Campaigns: do not apply campaigns in baskets configured to a supplier
- Admin: change service admin to list only providers that the current user can access
- Use UUID4 while generating order line ids by default
- Admin: Improve message banners, by:
    - Resetting the timeout for hiding the messages when a new message is added.
    - Immediately clearing the already hidden messages a when new one is added.
    - Not hiding messages when clicking just random background elements.
    - Allowing dismissing all of the messages by clicking any one of them anywhere.

### Added

- Admin: add improved product copy
- Core: add task runner to support running tasks using 3rd party services like Celery
- Core: add shops and supplier to ServiceProvider and Service models
- Front: add feature for checkout phases to spawn extra phases
- Add custom get_ip method and use it everywhere
- Importer: add permissions for all the diffrent types of importers
- Importer: add context class to data importer

### Removed

- Travis jobs for Django 1.8 and 1.9

### Fixed

- Removed the kind prefix from feedback messages using Django messages to prevent duplicate strings.
- Fixed the way the permissions identifier are split in admin
- Fixed issue that was importing User model directly
- Core: changed `del` basket command handler to not try to parse the basket line into an integer


## [1.10.16] - 2020-06-03

- Simple CMS: Fix a bug with the page links plugin

## [1.10.15] - 2020-06-02

### Changed

- Front: Ensure company name and tax number is set to both billing and shipping address same way
as when filled through company form when customer is not logged in. Company name and tax number
at order addresses seems to help with some taxation logic as well as makes things more consistent.

### Fixed

- Admin: Make sure related custom columns are added accrodingly. Fix issue with filtering through columns
that are by default hidden

## [1.10.14] - 2020-05-27

### Fixed

- Front: only show carousel title when there is one

### Changed

- Notify: Add AccountActivation event. AccountActivation event is
  triggered only when the user is activated for the first time.
- Front: improve next parameter with registration. Check GET
  parameter first and then fallback to POST data.

## [1.10.13] - 2020-05-20

- Admin: fix width issue with picotable images
- Admin: fix bugs in order edit and improve it one step closer to
  multivendor world. Now supports situation when vendors does not
  share products.
     - Add option to make shipping and payment method optional
     - Add supplier to pricing context
     - Show supplier name on product column
     - Make auto add for product select false by default
     - Fix product select2 missing URL and data handler since
       the whole ajax method was passed as attrs.
     - Add option to open/close collapsed content sections in mobile
- Core: add option to enable order edit for multiple vendors
- Front: do not stack history on product list when filters are changed.
  Instead replace state so back-buttons works nicely.
- Front: prevent image Lightbox touching history so you do not need
  to click back 6 times after you have viewed all images.

## [1.10.12] - 2020-05-05

### Added

- Admin: add error message when upload fails. At media queue complete do not
  resave product media if the file-count has not changed. This for example
  prevents media save when the upload itself fails.
- Admin: add option to override dropzone upload path by using data attribute
- Admin: add upload path to browser URLs and use it to fallback on media
  uploads when the actual media path is not available.
- Admin: Ability to delete manufacturer
- Admin: Ability to login as the selected contact if it's a user

### Fixed

- Admin: Now when activating/deactivating user it's contact will also change
- Admin: New notification for when a account get's reactivated

## [1.10.11] - 2020-04-23

### Fixed

- Discounts: create different admin module for archived discounts to fix breadcrumbs
- Fix product pagination by not overriding the state with undefined values

### Fixed

- Middleware: fix so it trys to take the users timezone first, then the suppliers, last the projects TIME_ZONE

### Changed

- Front: customize sort options through settings

## [1.10.10] - 2020-03-24

### Fixed

- Admin: Notification name when deleteing it
- Admin: Update contact list so that it only shows customers by default
- Front: Fix typo

### Changed

- Front: Add supplier choice to best selling product context function
- Admin: allow sorting categories by name
- Admin: show product orderability errors as list


## [1.10.9] - 2020-03-24

### Fixed

- Admin: remove pinned /sa/ URL from scripts to support dynamic admin URLs
- Admin: Fix graphical (incorrect indent) bug in Product / Stock Management

## [1.10.8] - 2020-03-20

### Changed

- Admin: add spinner and progressbar options components through Bootstrap 4.

### Fixed

- Issue running category filter browser test with Travis


## [1.10.7] - 2020-03-09

### Fixed

- Admin: remove pinned /sa/ URL from scripts to support dynamic admin URLs
- Front: keep the current query string parameters as the initial state
  when refreshing product filters.

### Changed

- Admin: fix page jumps after reaload
- Admin: make browser urls support urls with parameters

## [1.10.6] - 2020-02-28

### Changed

- Core: supplier name max length to 128 from 64

## [1.10.5] - 2020-02-27

### Added

- Add option to send notification event at password recovery

### Changed

- Improve the admin modals to use flexbox and work better on small devices

### Fixed

- Admin: fix password recovery success URL
- Picotable: render the filters button on small devices,
  even when there is no data, to allow resetting filters

## [1.10.4] - 2020-02-22

### Changed

- Make Admin messages dismissible

### Fixed

- Admin: Fix search results overflowing the canvas

## [1.10.3] - 2020-02-21

### Fixed

- Admin: fix bug when uploading product media

## [1.10.2] - 2020-02-19

### Added

- Admin: add option to impersonate staff users
- Notify: add option to delete notify scripts
- Admin: Allow shop staff to impersonate regular users
- Notify: Add BCC and CC fields to SendEmail notification action.
- Add the CHANGELOG.md to the root of the code base.

### Changed

- Xtheme: Improve template injection by checking not wasting time invoking regex for nothing
- Add `MiddlewareMixin` to all middlewares to prepare for Django 2.x
- Notify: Changed the Email topology type to support comma-separated list of emails when using constants.
- Front: skip product filter refresh if filters not defined
- GDPR: change "i agree" button to "i understand"

### Fixed

- Front: fix notification template default content
- Admin: improve primary image fallback for product
- Fixed the placeholder of Select2 component in Admin
- FileDnDUploader: Add check for the `data-kind` attribute of the drop zone. If the data-kind is
  `images`, add an attribute to the hidden input that only allows images to be uploaded.
- Front: fix bug with imagelightbox
- CMS: Free page URL on delete

## Older versions

Find older release notes [here](./doc/changelog.rst).
