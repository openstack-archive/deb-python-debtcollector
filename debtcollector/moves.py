# -*- coding: utf-8 -*-

#    Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import inspect

import six

from debtcollector import _utils

_KIND_MOVED_PREFIX_TPL = "%s '%s' has moved to '%s'"
_CLASS_MOVED_PREFIX_TPL = "Class '%s' has moved to '%s'"
_MOVED_METHOD_POSTFIX = "()"


def _moved_decorator(kind, new_attribute_name, message=None,
                     version=None, removal_version=None, stacklevel=3,
                     attr_postfix=None, category=None):
    """Decorates a method/property that was moved to another location."""

    def decorator(f):
        fully_qualified, old_attribute_name = _utils.get_qualified_name(f)
        if attr_postfix:
            old_attribute_name += attr_postfix

        @six.wraps(f)
        def wrapper(self, *args, **kwargs):
            base_name = _utils.get_class_name(self, fully_qualified=False)
            if fully_qualified:
                old_name = old_attribute_name
            else:
                old_name = ".".join((base_name, old_attribute_name))
            new_name = ".".join((base_name, new_attribute_name))
            prefix = _KIND_MOVED_PREFIX_TPL % (kind, old_name, new_name)
            out_message = _utils.generate_message(
                prefix, message=message,
                version=version, removal_version=removal_version)
            _utils.deprecation(out_message, stacklevel=stacklevel,
                               category=category)
            return f(self, *args, **kwargs)

        return wrapper

    return decorator


def moved_method(new_method_name, message=None,
                 version=None, removal_version=None, stacklevel=3,
                 category=None):
    """Decorates a *instance* method that was moved to another location."""
    if not new_method_name.endswith(_MOVED_METHOD_POSTFIX):
        new_method_name += _MOVED_METHOD_POSTFIX
    return _moved_decorator('Method', new_method_name, message=message,
                            version=version, removal_version=removal_version,
                            stacklevel=stacklevel,
                            attr_postfix=_MOVED_METHOD_POSTFIX,
                            category=category)


def moved_property(new_attribute_name, message=None,
                   version=None, removal_version=None, stacklevel=3,
                   category=None):
    """Decorates a *instance* property that was moved to another location."""
    return _moved_decorator('Property', new_attribute_name, message=message,
                            version=version, removal_version=removal_version,
                            stacklevel=stacklevel, category=category)


def moved_class(new_class, old_class_name, old_module_name,
                message=None, version=None, removal_version=None,
                stacklevel=3, category=None):
    """Deprecates a class that was moved to another location.

    This creates a 'new-old' type that can be used for a
    deprecation period that can be inherited from. This will emit warnings
    when the old locations class is initialized, telling where the new and
    improved location for the old class now is.
    """

    if not inspect.isclass(new_class):
        _qual, type_name = _utils.get_qualified_name(type(new_class))
        raise TypeError("Unexpected class type '%s' (expected"
                        " class type only)" % type_name)

    old_name = ".".join((old_module_name, old_class_name))
    new_name = _utils.get_class_name(new_class)
    prefix = _CLASS_MOVED_PREFIX_TPL % (old_name, new_name)
    out_message = _utils.generate_message(
        prefix, message=message, version=version,
        removal_version=removal_version)

    def decorator(f):

        @six.wraps(f, assigned=("__name__", "__doc__"))
        def wrapper(self, *args, **kwargs):
            _utils.deprecation(out_message, stacklevel=stacklevel,
                               category=category)
            return f(self, *args, **kwargs)

        return wrapper

    old_class = type(old_class_name, (new_class,), {})
    old_class.__module__ = old_module_name
    old_class.__init__ = decorator(old_class.__init__)
    return old_class
