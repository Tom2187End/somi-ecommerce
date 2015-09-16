# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.


def cache_translations(objects, languages=None, meta=None):
    """
    Cache translation objects in given languages to the objects in one fell swoop.
    This will iterate a queryset, if one is passed!

    :param objects: List or queryset of Translatable models
    :param languages: Iterable of languages to fetch. In addition, all "_current_language"s will be fetched
    :return: objects
    """
    if not objects:
        return objects
    languages = set(languages or ())
    if meta is None:
        meta = objects[0]._parler_meta.root  # work on base model by default
    xlate_model = meta.model

    object_map = dict((object.pk, object) for object in objects)
    languages.update(set(object._current_language for object in objects))
    master_ids = object_map.keys()
    for translation in xlate_model.objects.filter(master_id__in=master_ids, language_code__in=languages):
        master = object_map[translation.master_id]
        master._translations_cache[xlate_model][translation.language_code] = translation
        setattr(translation, translation.__class__.master.cache_name, master)
    return objects
