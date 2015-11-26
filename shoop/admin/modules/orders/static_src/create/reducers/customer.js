/**
 * This file is part of Shoop.
 *
 * Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
 *
 * This source code is licensed under the AGPLv3 license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {handleActions} from "redux-actions";

function clearExistingCustomer(state) {
    return _.assign({}, state, {id: null, name: null});
}

function setAddressProperty(state, {payload}) {
    const {type, field, value} = payload;
    const updates = {};
    const {billingAddress, shippingAddress, shipToBillingAddress} = state;
    switch (type) {
        case "billing":
            updates.billingAddress  = _.set(billingAddress, field, value);
            if (shipToBillingAddress) {
                updates.shippingAddress = _.set(shippingAddress, field, value);
            }
            break;
        case "shipping":
            updates.shippingAddress  = _.set(shippingAddress, field, value);
            break;
    }
    return _.assign({}, state, updates);
}

export default handleActions({
    setCustomer: ((state, {payload}) => payload),
    clearExistingCustomer,
    setAddressProperty,
    setAddressSavingOption: ((state, {payload}) => _.assign(state, {saveAddress: payload})),
    setShipToBillingAddress: ((state, {payload}) => _.assign(state, {shipToBillingAddress: payload})),
    setIsCompany: ((state, {payload}) => _.assign(state, {isCompany: payload}))
}, {
    id: null,
    name: "",
    saveAddress: false,
    shipToBillingAddress: false,
    isCompany: false,
    billingAddress: {},
    shippingAddress: {}
});
