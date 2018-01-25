# This file is part of Shuup.
#
# Copyright (c) 2012-2018, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.


class TaxableItem(object):
    @property
    def tax_class(self):
        """
        :rtype: shuup.core.models.TaxClass
        """
