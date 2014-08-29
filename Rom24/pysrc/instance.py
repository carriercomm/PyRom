"""
/***************************************************************************
 *  Original Diku Mud copyright (C) 1990, 1991 by Sebastian Hammer,        *
 *  Michael Seifert, Hans Henrik St{rfeldt, Tom Madsen, and Katja Nyboe.   *
 *                                                                         *
 *  Merc Diku Mud improvments copyright (C) 1992, 1993 by Michael          *
 *  Chastain, Michael Quan, and Mitchell Tse.                              *
 *                                                                         *
 *  In order to use any part of this Merc Diku Mud, you must comply with   *
 *  both the original Diku license in 'license.doc' as well the Merc       *
 *  license in 'license.txt'.  In particular, you may not remove either of *
 *  these copyright notices.                                               *
 *                                                                         *
 *  Much time and thought has gone into this software and you are          *
 *  benefitting.  We hope that you share your changes too.  What goes      *
 *  around, comes around.                                                  *
 ***************************************************************************/

/***************************************************************************
*   ROM 2.4 is copyright 1993-1998 Russ Taylor                             *
*   ROM has been brought to you by the ROM consortium                      *
*       Russ Taylor (rtaylor@hypercube.org)                                *
*       Gabrielle Taylor (gtaylor@hypercube.org)                           *
*       Brian Moore (zump@rom.org)                                         *
*   By using this code, you have agreed to follow the terms of the         *
*   ROM license, in the file Rom24/doc/rom.license                         *
***************************************************************************/
/************
 * Ported to Python by Davion of MudBytes.net
 * Using Miniboa https://code.google.com/p/miniboa/
 * Now using Python 3 version https://code.google.com/p/miniboa-py3/
 ************/
"""
__author__ = 'quixadhal'

import os
import json
from collections import OrderedDict, namedtuple
import re
import logging

logger = logging.getLogger()

import settings

'''For the instance dicts, we are not going to make another pointer, or copy, of
the original entity. We are going to alias, or bind, the specific entity
_instances[dict key] [entity] back to the original global_instances[dict key]
[entity] pointer. This will give us a shared alias, not a copy. Lets us do a clean
and simple subset dict of whatever we want, and not over-reference memory locations
directly.

We do this as the following:

given mob entity
mob.instance_id = 1000 (autogenerated)
instance.global_instances[mob.instance_id] = mob
merc.mob_instances[mob.instance_id] = instance.global_instances[mob.instance_id]

Any changes to mob will reflect in both dicts simultaneously

Likewise you can effect a change TO mob from accessing either dict:

>>>mob.name = 'bob'
>>>instance.global_instances[mob.instance_id].name
'bob'
>>>merc.mob_instances[mob.instance_id].name
'bob'
'''

max_instance_id = 0
previous_max_instance_id = 0

area_templates = {}
item_templates = {}
room_templates = {}
npc_templates = {}
shop_templates = {}

global_instances = {}  # This is the global instance list, the heart of the game data set

areas = {}
items = {}
rooms = {}
npcs = {}
shops = {}
players = {}
characters = {}  # This is PC and NPC combined

helps = {}
socials = {}
resets = {}

'''
Contains lists of instances,
Key: string VNUM
Value: list Instance_ID of object associated with Key:VNUM
'''
instances_by_area = {}
instances_by_item = {}
instances_by_room = {}
instances_by_npc = {}
instances_by_shop = {}
instances_by_player = {}

# Things to omit from instances that are in templates.
not_to_instance = []

def isnamedtuple(obj):
    """
    Named Tuples look, to python, like a normal tuple, so we have to poke around
    their innards a bit to see if they're actually the fancy version.

    :param obj: potential namedtuple container
    :type obj:
    :return: True if obj is a namedtuple
    :rtype: bool
    """
    return isinstance(obj, tuple) and \
           hasattr(obj, '_fields') and \
           hasattr(obj, '_asdict') and \
           callable(obj._asdict)


def to_json(data):
    """
    This function takes an arbitrary data object and attempts to return a JSON
    compatible dict-based structure, which from_json() can use to recreate the
    original object.

    :param data: data object to be serialized
    :type data:
    :return: JSON compatible data element
    :rtype:
    """

    # Order matters here.  It's important to immediately return a base type.
    if data is None or isinstance(data, (bool, int, float, str)):
        return data

    if isinstance(data, OrderedDict):
        return {
            "__type__/OrderedDict": [[to_json(k), to_json(v)] for k, v in data.items()]
        }

    # We MUST check for namedtuple() before ordinary tuples.
    # Python's normal checks can't tell the difference.
    if isnamedtuple(data):
        return {
            "__type__/namedtuple": {
                "type": type(data).__name__,
                "fields": list(data._fields),
                "values": [to_json(getattr(data, f)) for f in data._fields]
            }
        }

    if isinstance(data, set):
        return {
            "__type__/set": [to_json(val) for val in data]
        }

    if isinstance(data, tuple):
        return {
            "__type__/tuple": [to_json(val) for val in data]
        }

    if isinstance(data, list):
        return [to_json(val) for val in data]

    # Here, we return a plain dict if, and ONLY if, every key is a string.
    # JSON dicts require string keys... so otherwise, we have to manipulate.
    if isinstance(data, dict):
        if all(isinstance(k, str) for k in data):
            return {k: to_json(v) for k, v in data.items()}
        return {
            "__type__/dict": [[to_json(k), to_json(v)] for k, v in data.items()]
        }

    # Finally, the magic part.... if it wasn't a "normal" thing, check to see
    # if it has a to_json method.  If so, use it!
    if hasattr(data, 'to_json'):
        return data.to_json(to_json)

    # And if we still get nothing useful, PUNT!
    raise TypeError('Type %r not data-serializable' % type(data))


def from_json(data):
    """
    This function takes a JSON-encoded string and returns the original object
    it represents.

    :param data: JSON data chunks, passed in by json.loads()
    :type data:
    :return: An object
    :rtype:
    """

    # Order matters here.  It's important to immediately return a base type.
    if data is None or isinstance(data, (bool, int, float, str)):
        return data

    # Basic types we've labeled are easy to reconstruct.
    if "__type__/tuple" in data:
        return tuple(data["__type__/tuple"])

    if "__type__/set" in data:
        return set(data["__type__/set"])

    if "__type__/dict" in data:
        return dict(data["__type__/dict"])

    # In the case of an OrderedDict(), we just pass the data to the class.
    if "__type__/OrderedDict" in data:
        return OrderedDict(data["__type__/OrderedDict"])

    # For a namedtuple, we have to rebuild it as a class and then make an instance.
    if "__type__/namedtuple" in data:
        tmp = data["__type__/namedtuple"]
        return namedtuple(tmp["type"], tmp["fields"])(*tmp["values"])

    # If we're a dict, we can check to see if we're a custom class.
    # If we are, we need to find out class definition and make sure
    # there's a from_json() method to call.  If so, let it handle things.
    if hasattr(data, 'keys'):
        for k in data.keys():
            found = re.findall('__class__\/((?:\w+)\.)*(\w+)', k)
            if found:
                import importlib
                module_name = found[0][0].rstrip('.')
                class_name = found[0][1]

                if module_name != '' and class_name != '':
                    module_ref = importlib.import_module(module_name)
                    class_ref = getattr(module_ref, class_name)
                    if hasattr(class_ref, 'from_json'):
                        return class_ref.from_json(data, from_json)

    # If we have no idea, return whatever we are and hope someone else
    # will handle it up (or down) stream.
    return data


def save():
    os.makedirs(settings.INSTANCE_DIR, 0o755, True)
    filename = os.path.join(settings.INSTANCE_DIR, 'list.json')
    tmp_dict = {}
    for i in global_instances:
        if i in players:
            pass
        else:
            tmp_dict[i] = [global_instances[i].__module__, global_instances[i].__class__.__name__]
    with open(filename, 'w') as fp:
        json.dump({'max_instance_id': max_instance_id, 'data': tmp_dict}, fp, default=to_json, indent=4, sort_keys=True)

    for i in areas:
        areas[i].save(force=True)
    for i in rooms:
        rooms[i].save(force=True)
    for i in npcs:
        npcs[i].save(force=True)
    for i in players:
        players[i].save(force=True)
    for i in items:
        it = items[i]
        if it.in_living() is not None:
            continue
        if it.in_room() is not None:
            continue
        if it.in_item() is not None:
            continue
        it.save(force=True)


def load():
    filename = os.path.join(settings.INSTANCE_DIR, 'list.json')
    if os.path.isfile(filename):
        with open(filename, 'r') as fp:
            tmp_dict = json.load(fp, object_hook=from_json)
        global max_instance_id
        global global_instances
        max_instance_id = tmp_dict['max_instance_id']
        import importlib
        for k,v in tmp_dict['data']:
            module_ref = importlib.import_module(v[0])
            class_ref = getattr(module_ref, v[1])
            if hasattr(class_ref, 'load'):
                obj = class_ref.load(instance_id=k)
                if isinstance(obj, class_ref):
                    logger.boot('Restored instance %d (%r)', k, repr(obj))


class Instancer:
    def __init__(self):
        """Here is the backbone of our instancing. This function takes the global instance
        number and increments it. After dealing with the dicts for our objects, we will save
        the global instance number to a file, which will be important later when persistence
         is, or if someone wants to, be implemented.

        It is passed the object instance, for which we will make an identification.

        First we match the type we need to make, then add that to each dict that it needs to be in.

        As we are using just a single pointer between all of these dicts, we populate global_instances
        first, with a pointer to the object. The following dicts 'alias' their value to the value
        represented in global_instances[instance_id].

        This lets us maintain a single pointer, with windows to that single pointer from our sub dicts,
        allowing for a saner environment.

        This means that the destructor should destruct in reverse order, just in case."""
        super().__init__()
        self.instance_id = None

    def instancer(self):
        global max_instance_id, global_instances
        max_instance_id += 1
        if global_instances.get(max_instance_id, None):
            raise ValueError('houston we have a problem - instance number already in global instances')
        self.instance_id = max_instance_id
