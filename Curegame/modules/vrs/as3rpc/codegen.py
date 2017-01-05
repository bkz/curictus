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

import datetime
import inspect
import logging
import types
import os

import sqlalchemy as sa
import sqlalchemy.orm as orm

from vrs.db import has_one, has_many, computed_field, computed_array

_log = logging.getLogger('as3rpc')

##############################################################################
# Documentation/examples.
##############################################################################

#
# class EnumType(object):
#     __amf_class__ = "vrs.EnumType"
#     __amf_enum__  = str
#
#     VALUE_ONE = "identifier-a"
#     VALUE_TWO = "identifier-b"
#
#
# class DataType(object):
#     __amf_class__ = "vrs.DataType"
#
#     enum_value = computed_field(str)
#     ints_value = computed_field([int])
#
#     def __init__(self):
#         self.enum_value = EnumType.VALUE_ONE
#         self.ints_value = [1,2,3,4,5]
#
#     @classmethod
#     def __serialize__(cls):
#         return [SystemConfig.enum_value, SystemConfig.ints_value]
#

##############################################################################
# Class/Table -> AS3 mapping (code generation).
##############################################################################

class DeclaractionError(Exception):
    pass

as3_typemap = {
    bool                  : "Boolean",
    int                   : "int",
    long                  : "Number",
    float                 : "Number",
    str                   : "String",
    unicode               : "String",
    dict                  : "ObjectProxy",
    list                  : "ArrayCollection",
    tuple                 : "ArrayCollection",
    datetime.datetime     : "Date",
    sa.types.Boolean      : "Boolean",
    sa.types.Integer      : "Number",
    sa.types.String       : "String",
    sa.types.Date         : "Date",
    sa.types.DateTime     : "Date",
    sa.types.Time         : "Date",
    sa.types.Unicode      : "String",
    sa.types.UnicodeText  : "String",
    sa.types.LargeBinary  : "String",      # Assume UTF-8 storage.
    sa.types.PickleType   : "ObjectProxy", # Assume JSON storage.
}


def is_valid_py_type(pytype):
    allowed_types = [
        bool, int, long, float,
        str, unicode,
        list, tuple, dict,
        datetime.datetime]
    if type(pytype) is list:
        if len(pytype) > 0:
            return (pytype[0] in allowed_types)
        else:
            return True
    elif type(pytype) is dict:
        return True
    else:
        return any([(pytype is x) for x in allowed_types])


def is_valid_sa_type(satype):
    allowed_types = [
        sa.types.String,
        sa.types.Integer,
        sa.types.SmallInteger,
        sa.types.Numeric,
        sa.types.Float,
        sa.types.DateTime,
        sa.types.Date,
        sa.types.Time,
        sa.types.Binary,
        sa.types.Boolean,
        sa.types.Unicode,
        sa.types.UnicodeText,
        sa.types.LargeBinary,
        sa.types.PickleType]
    if satype not in allowed_types and hasattr(satype, 'impl'):
        if is_valid_sa_type(satype.impl):
            as3_typemap[satype] = as3_typemap[satype.impl]
            return True
    return satype in allowed_types


def is_valid_type(decl):
    if type(decl) is list and len(decl) > 0:
        decl = decl[0]
    return is_amf_type(decl) or is_amf_enum(decl) or is_valid_sa_type(decl) or is_valid_py_type(decl)


def getattr_from_value(obj, value):
    for attr in dir(obj):
        if getattr(obj, attr) is value:
            return attr
    return None


def is_amf_type(obj):
    return hasattr(obj, '__amf_class__')


def is_amf_enum(obj):
    return hasattr(obj, '__amf_enum__')


def is_amf_service(obj):
    return hasattr(obj, '__amf_service__')


def get_enum_type(obj):
    assert is_amf_enum(obj)
    return obj.__amf_enum__


def get_amf_import(obj):
    assert is_amf_type(obj)
    return obj.__amf_class__


def get_amf_classname(obj):
    assert is_amf_type(obj)
    return get_amf_import(obj).rsplit(".", 1)[1]


def get_amf_package(obj):
    assert is_amf_type(obj)
    return get_amf_import(obj).rsplit(".", 1)[0]


def is_array(obj):
    return type(obj) in [list, tuple]


def get_array_type(a):
    assert is_array(a)
    if len(a) > 0:
        return a[0]
    else:
        return None


def get_as3_type(pytype):
    try:
        if type(pytype) is list:
            return "ArrayCollection"
        if is_amf_enum(pytype):
            return as3_typemap[get_enum_type(pytype)]
        if is_amf_type(pytype):
            return get_amf_classname(pytype)
        return as3_typemap[pytype]
    except KeyError:
        return "Object"


def get_as3_import(pytype):
    if type(pytype) is list:
        if len(pytype) > 0 and is_amf_type(pytype[0]):
            return get_amf_import(pytype[0])
        else:
            return None
    if is_amf_type(pytype):
        return get_amf_import(pytype)
    else:
        return None


def generate_as3(klass, import_packages, import_classes, constants, enum_vars, typed_vars, untyped_arrays, typed_arrays, typed_arraycollections):
    output = []
    def indent(level, fmt, *args):
        output.append(4 * level * ' ' + (fmt % args))
    if klass.__doc__:
        for line in [line.lstrip() for line in klass.__doc__.split("\n")]:
            indent(0, "// %s" % line)
    indent(0, "package %s" % get_amf_package(klass))
    indent(0, "{")
    if import_packages:
        for package in sorted(tuple(import_packages)):
            indent(1, "import %s;" % package)
        indent(0, "")
    if import_classes:
        for import_classtype in sorted(tuple([get_amf_import(c) for c in import_classes])):
            indent(1, "import %s;" % import_classtype)
        indent(0, "")
    indent(1, "[Bindable]")
    indent(1, "[RemoteClass(alias=\"%s\")]" % get_amf_import(klass))
    indent(1, "public class %s" % get_amf_classname(klass))
    indent(1, "{")
    for (field_name, constant_value) in constants.iteritems():
        fmt_value = constant_value
        if type(fmt_value) is str:
            fmt_value = "\"" + fmt_value + "\""
        indent(2, "public static const %s:%s = %s;" % (field_name, get_as3_type(type(constant_value)), fmt_value))
    for (field_name, enum_type, enum_class) in sorted(enum_vars):
        indent(2, "public var %s:%s; // @enum of %s" % (field_name, get_as3_type(enum_type), get_as3_import(enum_class)))
    for (field_name, field_type) in sorted(typed_vars):
        indent(2, "public var %s:%s;" % (field_name, get_as3_type(field_type)))
    for field_name in sorted(untyped_arrays):
        indent(2, "public var %s:ArrayCollection;" % field_name)
    if typed_vars or untyped_arrays:
        indent(2, "")
    for (field_name, field_type) in sorted(typed_arrays):
        indent(2, "[ArrayElementType(\"%s\")]" % get_as3_type(field_type))
        indent(2, "public var %s:ArrayCollection;" % field_name)
        indent(2, "")
    for (field_name, field_type) in sorted(typed_arraycollections):
        indent(2, "[ArrayElementType(\"%s\")]" % get_as3_import(field_type))
        indent(2, "public var %s:ArrayCollection;" % field_name)
        indent(2, "")
    indent(1, "}")
    indent(0, "}")
    return "\n".join(output)


def register_enum(klass, srcpath=None):
    assert is_amf_type(klass)
    assert is_amf_enum(klass)
    enum_type = get_enum_type(klass)
    assert enum_type in [int, str]

    constants = {}
    for attr in [attr for attr in dir(klass) if attr[:1] != "_"]:
        attr_value = getattr(klass, attr)
        if inspect.isfunction(attr_value) or inspect.ismethod(attr_value):
            continue
        if type(attr_value) is not enum_type:
            raise DeclaractionError("Enum constant %s.%s must must match declared enum type %s" % (klass.__name__, attr, enum_type))
        constants[attr] = attr_value

    import_packages, import_classes = [], []
    enum_vars, typed_vars, untyped_arrays, typed_arrays, typed_arraycollections = [], [], [], [], []

    if srcpath:
        packagedir = os.path.abspath(os.path.join(srcpath, get_amf_package(klass).replace(".", "/")))
        if not os.path.exists(packagedir):
            os.makedirs(packagedir)

        output = generate_as3(
            klass, import_packages, import_classes,
            constants, enum_vars, typed_vars, untyped_arrays,
            typed_arrays, typed_arraycollections)

        classfile = os.path.join(packagedir, get_amf_classname(klass) + ".as")
        if os.path.exists(classfile) and open(classfile, "rt").read() == output:
            _log.debug("Skipping enum: %s" % classfile)
        else:
            _log.debug("Generating enum: %s" % classfile)
            open(classfile, "wt").write(output)


def register_class(klass, srcpath=None):
    if not hasattr(klass, '__amf_class__'):
        raise DeclaractionError("%s is missing AMF class attribute" % klass.__name__)
    if not hasattr(klass, '__serialize__'):
        raise DeclaractionError("%s is missing AMF serialization class/static method" % klass.__name__)
    serialize_typemap = {}
    for column in klass.__serialize__():
        column_attr = getattr_from_value(klass, column)
        if column_attr is None:
            raise DeclaractionError("Unknown column in %s AMF serialization specification" % klass.__name__)
        elif is_amf_enum(column):
            column_type = column
            serialize_typemap[column_attr] = column_type
        elif type(column) is computed_field:
            column_type = column.field_type
            serialize_typemap[column_attr] = column_type
        elif type(column) is computed_array:
            array_type = column.field_type
            serialize_typemap[column_attr] = [array_type]
        elif is_amf_type(column):
            column_type = column
            serialize_typemap[column_attr] = column_type
        else:
            try:
                prop = klass.__mapper__.get_property(column.key)
            except AttributeError:
                raise DeclaractionError("%s.%s is not a valid sqlalchemy column" % (klass.__name__, column_attr))
            if isinstance(prop, orm.properties.ColumnProperty):
                column_type = prop.columns[0].type.__class__
                serialize_typemap[column_attr] = column_type
            elif isinstance(prop, orm.properties.RelationProperty):
                column_type = prop.argument
                if type(column_type) is types.FunctionType:
                    column_type = column_type()
                if prop.uselist == False:
                    serialize_typemap[column_attr] = column_type
                else:
                    serialize_typemap[column_attr] = [column_type]
            else:
                raise DeclaractionError("Unknown sqlalchemy column type for %s.%s" % (klass.__name__, column_attr))
        assert is_valid_type(column_type)

    klass.__amf_attrs__ = serialize_typemap.keys()

    import_packages, import_classes = [], []
    enum_vars, typed_vars, untyped_arrays, typed_arrays, typed_arraycollections = [], [], [], [], []
    constants = {}

    for (field_name, field_type) in serialize_typemap.iteritems():
        if is_amf_enum(field_type):
            # typed enumeration of user type
            enum_type = get_enum_type(field_type)
            enum_vars.append([field_name, enum_type, field_type])
            import_classes.append(field_type)
        elif is_array(field_type):
            array_type = get_array_type(field_type)
            if array_type:
                if is_amf_type(array_type):
                    # typed array-collcetion of user type
                    typed_arraycollections.append([field_name, array_type])
                    import_packages.append("mx.collections.ArrayCollection")
                    import_classes.append(array_type)
                else:
                   # typed array of builtin type
                    typed_arrays.append([field_name, array_type])
            else:
                # untyped object array
                untyped_arrays.append(field_name)
        else:
            if is_amf_type(field_type):
                # field of user type
                typed_vars.append([field_name, field_type])
                import_classes.append(field_type)
            else:
                # field of builtin type
                typed_vars.append([field_name, field_type])

    klass.__amf_imports__ = sorted(set([get_amf_import(c) for c in import_classes]))

    if srcpath:
        packagedir = os.path.abspath(os.path.join(srcpath, get_amf_package(klass).replace(".", "/")))
        if not os.path.exists(packagedir):
            os.makedirs(packagedir)

        output = generate_as3(
            klass, import_packages, import_classes,
            constants, enum_vars, typed_vars, untyped_arrays,
            typed_arrays, typed_arraycollections)

        classfile = os.path.join(packagedir, get_amf_classname(klass) + ".as")
        if os.path.exists(classfile) and open(classfile, "rt").read() == output:
            _log.debug("Skipping class: %s" % classfile)
        else:
            _log.debug("Generating class: %s" % classfile)
            open(classfile, "wt").write(output)


##############################################################################
# Python -> AS3 (Flex) Service mapper.
##############################################################################

class ArgumentTypeError(Exception):
    pass


class ReturnTypeError(Exception):
    pass


class remotemethod(object):
    def __init__(self, result_type, **kwargs):
        self.result_type, self.arg_types = result_type, kwargs
        if self.result_type is str:
            self.result_type = unicode

    def __call__(self, fn):
        def wrapper(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
            except Exception, e:
                logging.exception("rpc error")
                raise
            if type(result) is str:
                result = unicode(result)
            if type(self.result_type) is list:
                if type(result) is not list:
                    raise ReturnTypeError("%s returned, expecting a list of %s" % (type(result), self.result_type))
                if len(self.result_type) > 0 and len(result) > 0:
                    pass
            else:
                if type(result) is not self.result_type:
                    raise ReturnTypeError("%s returned, expecting %s" % (type(result), self.result_type))
            return result

        code = fn.func_code
        argcount = code.co_argcount
        argnames = code.co_varnames[1:argcount]
        self.arg_types = [[arg_name, self.arg_types[arg_name]] for arg_name in argnames]

        wrapper._result_type = self.result_type
        wrapper._arg_types = self.arg_types
        wrapper.__doc__ = fn.__doc__
        wrapper.__name__ = fn.__name__
        wrapper.__module__ = fn.__module__
        try:
            wrapper.__line__ = inspect.getsourcelines(fn)[1]
        except IOError:
            wrapper.__line__ = 0 # Source file probably not available.
        return wrapper


as3_service_template = """\
package %s
{
    import mx.utils.ObjectProxy;
    import mx.collections.ArrayCollection;
    import mx.collections.ItemResponder;

    import mx.messaging.ChannelSet;
    import mx.messaging.channels.AMFChannel;

    import mx.rpc.AbstractOperation;
    import mx.rpc.AsyncToken;
    import mx.rpc.remoting.mxml.RemoteObject;

    import mx.rpc.events.FaultEvent;
    import mx.rpc.events.ResultEvent;

%s

    public class %s
    {
        protected var _service:RemoteObject;
        protected var _exceptionHandler:Function;

        /**
         * Connect service instance to AMF endpoint at ``url``. Optionally specify a  global
         * ``exceptionHandler`` which is shared by all service methods where a custom onError()
         * callback isn't specified. If neither a custom exception handler or a per-call
         * onError() is passed, a default handler will be used which throws an Error() instead.
         * If you wish to override the standard busy cursor behaviour (change the cursor and block
         * the UI until requests fails or completes) set ``showBusyCursor`` to false.
         *
         * exceptionHandler = function(method:String, exceptionType:String, exceptionMessage:String)
         *
         * @return True/False to signal if successsfully connected or not.
         */
        public function connect(url:String, exceptionHandler:Function = null, showBusyCursor:Boolean = true):Boolean
        {
            if (_service == null)
            {
                var channel:AMFChannel = new AMFChannel("amf-channel", url);

                var channels:ChannelSet = new ChannelSet();
                channels.addChannel(channel);

                _service = new RemoteObject(\"%s\");
                _service.showBusyCursor = showBusyCursor;
                _service.channelSet = channels;
            }

            if (exceptionHandler != null) {
                _exceptionHandler = exceptionHandler;
            }
            else {
                _exceptionHandler = defaultExceptionHandler;
            }

            return true;
        }

        /**
         * Default exception handler for AMF remote call failures, see connect() for details.
         */
        protected function defaultExceptionHandler(method:String, exceptionType:String, exceptionMessage:String):void
        {
            throw Error(exceptionType + " in " + method + " (" + exceptionMessage + ")");
        }

        ////////////////////////////////
        // Service API methods.
        ////////////////////////////////
%s
    }
}
"""

as3_service_method = """
        public function %s(%sonComplete:Function = null, onError:Function = null):void
        {
            var method:AbstractOperation = _service.getOperation("%s");

            var token:AsyncToken = method.send(%s);

            token.addResponder(new ItemResponder(
                function(event:ResultEvent, token:AsyncToken):void {
                    var result:%s = event.result as %s;
                    if (onComplete != null)
                        onComplete(result);
                },
                function(event:FaultEvent, token:AsyncToken):void {
                    if (onError != null)
                        onError(event.fault as Error);
                    else if (_exceptionHandler != null)
                        _exceptionHandler("%s.%s", event.fault.faultCode, event.fault.faultString);
                },
                token));
        }
"""


def list_methods(klass):
    def getline(fn):
        try:
            return fn.__line__
        except AttributeError:
            return -1
    methods = inspect.getmembers(klass, inspect.ismethod)
    return sorted(methods, key=lambda(name,func):getline(func))


def register_service(klass, srcpath=None):
    if not hasattr(klass, '__amf_service__'):
        raise DeclaractionError("%s is missing AMF class attribute" % klass.__name__)
    klass.__amf_class__ = klass.__amf_service__
    klass.__amf_methods__ = []
    klass.__amf_imports__ = []
    imports = []
    service_code = ""
    for (method_name, method) in list_methods(klass):
        try:
            result_type = method._result_type
            arg_types = method._arg_types
        except AttributeError:
            continue
        if not is_valid_type(result_type):
            raise ArgumentTypeError("%s.%s has invalid return type %s" % (klass.__name__, method_name, result_type))
        package = get_as3_import(result_type)
        if package:
            imports.append(package)
        for (arg_name, arg_type) in arg_types:
            if not is_valid_type(arg_type):
                raise ArgumentTypeError("Argument '%s' for %s.%s is invalid (%s)" % (arg_name, klass.__name__, method_name, arg_type))
            package = get_as3_import(arg_type)
            if package:
                imports.append(package)
        argspec = ", ".join(["%s:%s" % (k, get_as3_type(v)) for (k,v) in arg_types])
        if argspec:
            argspec += ", "
        args = ", ".join([k for (k,v) in arg_types])
        result_type_as3 = get_as3_type(result_type)
        method_comment = "\n"
        method_comment += "%s/**\n" % (8 * ' ')
        method_comment += "%s * Method: %s\n" % (8 * ' ', method_name)
        method_comment += "%s *\n" % (8 * ' ')
        if method.__doc__:
            lines = [line.strip() for line in method.__doc__.split("\n")]
            if len(lines) > 0 and lines[0] == "":
                lines = lines[1:]
            if  len(lines) > 0 and lines[-1] == "":
                lines = lines[:-1]
            if len(lines) > 0:
                for line in lines:
                    method_comment += "%s * %s\n" % (8 * ' ', line)
                method_comment += "%s * \n" % (8 * ' ')
        have_enum_args = False
        for (k,v) in arg_types:
            if is_amf_enum(v):
                method_comment += "%s * @param %s\n" % (8 * ' ', k)
                method_comment += "%s *   enum of %s\n" % (8 * ' ', get_as3_import(v))
                have_enum_args = True
        if have_enum_args:
            method_comment += "%s * \n" % (8 * ' ')
        if is_array(result_type) and len(result_type) > 0:
            array_type_as3 = get_as3_type(result_type[0])
            method_comment += "%s * @param onComplete :\n" % (8 * ' ')
            method_comment += "%s *   [ArrayElementType(\"%s\")]\n" % (8 * ' ', array_type_as3)
            method_comment += "%s *   function(result:%s):void {}\n" % (8 * ' ', result_type_as3)
        elif is_amf_enum(result_type):
            enum_type_as3 = get_as3_type(get_enum_type(result_type))
            enum_import_as3 = get_as3_import(result_type)
            method_comment += "%s * @param onComplete\n" % (8 * ' ')
            method_comment += "%s *   function(result:%s):void {} => enum of %s\n" % (8 * ' ', enum_type_as3, enum_import_as3)
        else:
            method_comment += "%s * @param onComplete\n" % (8 * ' ')
            method_comment += "%s *   function(result:%s):void {}\n" % (8 * ' ', result_type_as3)
        method_comment += "%s * \n" % (8 * ' ')
        method_comment += "%s * @param onError\n" % (8 * ' ')
        method_comment += "%s *   function(e:Error):void {}\n" % (8 * ' ')
        method_comment += "%s */" % (8 * ' ')
        service_code += method_comment
        service_code += as3_service_method % (method_name, argspec, method_name, args, result_type_as3, result_type_as3, get_amf_classname(klass), method_name)
        klass.__amf_methods__.append(method_name)

    klass.__amf_imports__ = sorted(set(imports))

    if srcpath:
        packagedir = os.path.abspath(os.path.join(srcpath, get_amf_package(klass).replace(".", "/")))
        if not os.path.exists(packagedir):
            os.makedirs(packagedir)

        class_name = get_amf_classname(klass)
        class_package = get_amf_package(klass)
        class_imports = "\n".join(["    import %s;" % package for package in klass.__amf_imports__])

        service_output = as3_service_template % (class_package, class_imports, class_name, class_name, service_code)

        class_file = os.path.join(packagedir, class_name + ".as")
        if os.path.exists(class_file) and open(class_file, "rt").read() == service_output:
            _log.debug("Skipping service: %s" % class_file)
        else:
            _log.debug("Generating service: %s" % class_file)
            open(class_file, "wt").write(service_output)


##############################################################################
# The End.
##############################################################################
