##############################################################################
#
# Copyright (c) 2006-2011 Curictus AB.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##############################################################################

import logging
import gc, inspect

from amfast.class_def import ClassDefMapper, ClassDef
from amfast.class_def.sa_class_def import SaClassDef
from amfast.remoting import Service, CallableTarget

import codegen

_log = logging.getLogger('client')

##############################################################################
# Utilities.
##############################################################################

def find_pytype(as3import):
    for klass in [x for x in gc.get_objects() if inspect.isclass(x)]:
        if codegen.is_amf_type(klass) and codegen.get_amf_import(klass) == as3import:
            return klass
    return None


def register_type(klass, class_mapper, srcpath=None):
    if codegen.is_amf_enum(klass):
        codegen.register_enum(klass, srcpath)
    elif codegen.is_amf_type(klass):
        codegen.register_class(klass, srcpath)
        if hasattr(klass, '__mapper__'):
            class_mapper.mapClass(SaClassDef(klass, alias=klass.__amf_class__, static_attrs=klass.__amf_attrs__))
        else:
            class_mapper.mapClass(ClassDef(klass, alias=klass.__amf_class__, static_attrs=klass.__amf_attrs__))
        for as3import in klass.__amf_imports__:
            pytype = find_pytype(as3import)
            assert pytype is not None
            register_type(pytype, class_mapper, srcpath)


##############################################################################
# VRS AS3 RPC -> Tornado/AMFast service.
##############################################################################

def bind_amfast_service(klass, channel_set, class_mapper, args=[], srcpath=None):
    codegen.register_service(klass, srcpath)
    instance = klass(*args)
    service  = Service(klass.__name__)

    for method_name in klass.__amf_methods__:
        service.mapTarget(CallableTarget(getattr(instance, method_name), method_name))

    channel_set.service_mapper.mapService(service)

    for as3import in klass.__amf_imports__:
        pytype = find_pytype(as3import)
        assert pytype is not None
        register_type(pytype, class_mapper, srcpath=srcpath)


##############################################################################
# The End.
##############################################################################
