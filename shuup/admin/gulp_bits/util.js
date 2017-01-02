/**
 * This file is part of Shuup.
 *
 * Copyright (c) 2012-2017, Shoop Commerce Ltd. All rights reserved.
 *
 * This source code is licensed under the OSL-3.0 license found in the
 * LICENSE file in the root directory of this source tree.
 */
var path = require("path");

function basifyFile(spec, file) {
    if (!spec.base) {
        return file;
    }
    return path.join(spec.base, file);
}

function basifyFiles(spec) {
    return spec.files.map(basifyFile.bind(null, spec));
}

module.exports.basifyFile = basifyFile;
module.exports.basifyFiles = basifyFiles;
