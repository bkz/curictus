##############################################################################
#
# Copyright (c) 2006-2011 Curictus AB.
#
# This file part of Curictus VRS.
#
# Curictus VRS is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Curictus VRS is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Curictus VRS; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
#
##############################################################################

import os
import bpy
import xml.dom.minidom
import math
import mathutils

DEG2RAD = math.pi / 180.0
DECIMAL_PRECISION = 6

###########################################################################
# Export a Blender scene to the HGT X3D format.
#
# Primary design goal: WYSIWYG
# Secondary design goal: KISS
# Ternary design goal: 1-to-1 mapping between Blender and HGT X3D scenes
#
# RuntimeErrors are raised to notify the user of export limitations with
# a popup window (which does not appear, check console window after export
# until this issue has been fixed in Blender). Ideally, this should be
# checked by the custom Blender GUI extensions (todo).
#
# When envisioning Blender's 3D space, think of the xy-plane as the floor,
# with z pointing upwards. Implication: in HGT's _default_ viewpoint, you
# are looking down at the floor from above. You are _not_ sitting at a table
# looking forward. This is important.
#
# What works (tested):
#   * Quad Meshes
#   * Non-blended sky (one color) rendered correctly
#   * Subdivision surface modifier
#   * Point/Sun lamps with constant falloff
#   * Materials (with color corrections)
#   * Parenting to empties (nested)
#   * Text
#   * UV maps
#   * Empties and Transforms are exported as composed nodes:
#       <ToggleGroup DEF="ToggleGroup_OBJECT">
#           <Transform DEF="Transform_OBJECT"> ...
#
#   * DynamicTransforms in composed empties ("hgt_DynamicTransform" in object)
#   * SmoothSurface/Frictional Surface ("SS"/"FS" in object)
#
# Some things we can't handle correctly (yet):
#   * Spotlights
#   * Bump maps / normal maps
#   * Blended sky (two colors) rendered incorrectly (no blend, just horizon)
#   * Ambient colors
#   * Use Blender Camera/viewpoint
#   * Multiple lines in Text nodes
#
# Things that probably never will be handled due to X3D/H3D limitations:
#   * Multiple materials (use parented objects instead)
###########################################################################

# Let's try to be pep8 compliant this time, shall we? (not there yet)

class HGTExporter:
    def __init__(self, context, filepath, pyfilepath, options):
        self.context = context
        self.filepath = filepath
        self.pyfilepath = pyfilepath
        self.scene = context.scene
        self.options = options

        self.pre_check()

        self.xml = xml.dom.minidom.Document()

        self._materials = {}
        self._def_names = {}
        self._object_names = {}
        self._imagetextures = {}

        self. _object_renderers = {
            "LAMP": self.render_lamp,
            #"TEXT": self.render_text,
            "FONT": self.render_text,
            "EMPTY": self.render_empty,
            "MESH": self.render_mesh,

            "CURVE": self.render_mesh,
            "SURFACE": self.render_mesh,
            "META": self.render_mesh,

        }

    # Check that Blender Scene is properly set up
    def pre_check(self):
        if self.scene.unit_settings.system != "METRIC":
            raise RuntimeError("Scene Units must be set to METRIC")

    def export(self):
        tree = Tree(context = self.context)

        # Root node
        xmlroot = self.xel("Transform")
        xmlroot.setAttribute("DEF", "HGT_BASE_TRANSFORM")

        """
        # For now, write hardcoded Viewpoint
        vp  = self.xel("Viewpoint")
        vp.setAttribute("DEF", "CAMERA_HGT")
        vp.setAttribute("position", "0.0 -0.5 0.0")
        vp.setAttribute("orientation", "1.0 0.0 0.0 1.57079633")
        vp.setAttribute("fieldOfView", "0.582913588956")
        xmlroot.appendChild(vp)
        """

        if not self.options[("is_stylus")]:
            xmlroot.appendChild(self.render_background())

        # Recursively build scene nodes
        for oc in tree.root:
            xmlroot.appendChild(self.dump_tree_rec(oc, 1))

        # Write formatted result to file handle
        print("Exporting to filepath %s" % self.filepath)
        fh = open(self.filepath, 'wb')
        x = xmlroot.toprettyxml()
        fh.write(x.encode('utf8'))
        fh.close()

        if self.options[("use_sidecar")]:
            print("Writing sidecar...")
            self.write_sidecar()
        else:
            print("Skipping sidecar.")

    def write_sidecar(self):
        # Write sidecar .py file
        fh = open(self.pyfilepath, 'wb')
        fh.write(self.utf_string("# This is an auto-generated file. Do not edit manually.\n"))
        fh.write(self.utf_string("import hgt\n"))
        fh.write(self.utf_string("from hgt.blenderhelpers import get_world_and_nodes\n"))
        fh.write(self.utf_string("hgt_filename = '%s'\n" % (os.path.basename(self.filepath))))

        # Object names dict
        fh.write(self.utf_string("\nhgt_object_names = {}\n"))
        for name in sorted(self._object_names.keys()):
            fh.write(self.utf_string("hgt_object_names['%s'] = None\n" % (name)))

        # Object dict
        fh.write(self.utf_string("\nhgt_objects = {}\n"))
        for name in sorted(self._def_names.keys()):
            fh.write(self.utf_string("hgt_objects['%s'] = None\n" % (name)))

        fh.write(self.utf_string("(world, nodes) = get_world_and_nodes(hgt_filename, hgt_objects)\n"))
        fh.close()

    def utf_string(self, s):
        return s.encode('utf8')

    def dump_tree_rec(self, oc, indent):
        # Create xml node
        el = self.create_xml_node(oc.object)

        # Populate name dict
        name = oc.object.name
        if name in self._object_names:
            raise RuntimeError('Despite really anal checking, we discovered a duplicate object: %s' % name)
        else:
            self._object_names[name] = 'Fluuurp!!' # dummy val, unused for now

        # Recurse
        if len(oc.children) > 0:
            for ocChild in oc.children:
                el.appendChild(self.dump_tree_rec(ocChild, indent + 1))

        return el

    def create_xml_node(self, ob):
        if ob.type in self._object_renderers:
            return self._object_renderers[ob.type](ob)
        else:
            raise RuntimeError("No renderer for object type: %s" % ob.type)
            """
            print("Warning: No renderer for object type: %s" % ob.type)
            g = self.xel("Group")
            g.setAttribute("DEF", "%s_%s_DEBUG" % (ob.type, ob.name))
            return g
            """
    def render_lamp(self, ob):
        # http://wiki.blender.org/index.php/Doc:Manual/Lighting/Lights/Light_Attenuation
        if ob.data.type == "SUN":
            el = self.xel("DirectionalLight")
            el.setAttribute("DEF", self.create_def_name(ob, "DirectionalLight"))
            el.setAttribute("color", self.color_string(tuple(ob.data.color)))
            el.setAttribute("intensity", self.strfloat(ob.data.energy))
            m = ob.matrix_local.to_quaternion().to_matrix()
            v = mathutils.Vector((0, 0, -1))
            d = v * m
            el.setAttribute("direction", "%f %f %f" % tuple(d))

        elif ob.data.type == "POINT":
            el = self.xel("PointLight")
            el.setAttribute("DEF", self.create_def_name(ob, "PointLight"))
            #el.setAttribute("radius", str(ob.data.distance)) # radius field not used by H3D
            el.setAttribute("color", self.color_string(tuple(ob.data.color)))
            t = ob.matrix_local.to_translation()
            el.setAttribute("location", "%f %f %f" % tuple(t))

            energy = ob.data.energy
            distance = ob.data.distance
            la = ob.data.linear_attenuation
            qa = ob.data.quadratic_attenuation

            if ob.data.falloff_type == "CONSTANT":
                el.setAttribute("attenuation", "1 0 0")
            else:
                raise RuntimeError("Unsupported falloff type for lamp %s" % ob.name)

            # TODO: figure out what the equations should be to properly match Blender's lamps
            """
            elif ob.data.falloff_type == "INVERSE_LINEAR":
                el.setAttribute("attenuation", "0 %f 0" % (1.0 / distance))
            elif ob.data.falloff_type == "INVERSE_QUADRATIC":
                el.setAttribute("attenuation", "0 0 1")
            elif ob.data.falloff_type == "LINEAR_QUADRATIC_WEIGHTED":
                el.setAttribute("attenuation", "%f %f %f" % (0.0, ob.data.linear_attenuation, ob.data.quadratic_attenuation))
            """

            el.setAttribute("intensity", self.strfloat(energy))
            #el.setAttribute("ambientIntensity", str(ob.data.energy))
        else:
            raise RuntimeError("Unsupported lamp type for %s" % ob.name)

        return el

    def render_mesh(self, ob):
        return self.render_mesh_object(ob)

    def render_mesh_object(self, ob):
        el = self.render_transform(ob)
        shape = self.xel("Shape")
        el.appendChild(shape)

        material = self.render_material(ob)
        appearance = self.xel("Appearance")
        appearance.setAttribute("DEF", self.create_def_name(ob, "Appearance"))

        appearance.appendChild(material)
        shape.appendChild(appearance)

        # Look in object's custom properties for haptic surface
        # TODO: Replace these when Blender UI is mature.
        if "FS" in ob:
            frictionalSurface = self.xel("FrictionalSurface")
            frictionalSurface.setAttribute("staticFriction", "0.8")
            frictionalSurface.setAttribute("dynamicFriction", "0.4")
            frictionalSurface.setAttribute("stiffness", "0.6")
            frictionalSurface.setAttribute("damping", "0.5")
            frictionalSurface.setAttribute("useRelativeValues", "true")
            frictionalSurface.setAttribute("DEF", self.create_def_name(ob, "FrictionalSurface"))
            appearance.appendChild(frictionalSurface)
        if "SS" in ob:
            smoothSurface = self.xel("SmoothSurface")
            smoothSurface.setAttribute("DEF", self.create_def_name(ob, "SmoothSurface"))
            appearance.appendChild(smoothSurface)

        # TODO: The logic below is a bit complicated, mainly because we're
        # trying to save some megabytes by using USE instead of redefining
        # objects. Try to simplify the code.

        mat = ob.data.materials[0] # Assumed existing, render_materials above raises error if not

        # Apply modifiers to mesh data, matching Blender's preview for subdivision surfaces etc.
        # real_mesh = ob.data
        mesh = ob.to_mesh(self.scene, True, 'PREVIEW')

        # IndexedFaceSet
        indexedFaceSet = self.xel("IndexedFaceSet")
        shape.appendChild(indexedFaceSet)

        # Check if mesh has been DEF'd already
        mname = "Mesh_" + ob.data.name
        if mname in self._def_names:
            indexedFaceSet.setAttribute("USE", mname)

            if mat.use_face_texture:
                active_textures = mesh.uv_textures.active.data
                if len(active_textures) > 0:
                    tex = active_textures[0]
                    if tex.use_image:
                        imageTexture = self.render_image_texture(tex)
                        appearance.appendChild(imageTexture)
                    else:
                        raise RuntimeError("We've run into some trouble with the ImageTextures...")

            # NOTE: Return statement here because right now we're too lazy to
            # indent the block below.
            return el

        # ************************************

        # NOTE: else
        indexedFaceSet.setAttribute("DEF", self.create_def_name(ob.data, "Mesh"))

        # ImageTextures
        if mat.use_face_texture:
            active_textures = mesh.uv_textures.active.data
            if len(active_textures) > 0:
                imageTextures = []
                textureCoordinates = []
                textureCoordinateIndices = []
                j = 0
                for tex in active_textures:
                    if tex.use_image:
                        imageTextures.append(self.render_image_texture(tex))
                    else:
                        raise RuntimeError("Object %s is missing an image in active_textures" % ob.name)

                    for uv in tex.uv:
                        textureCoordinates.append("%.6f %.6f" % tuple(uv))
                        textureCoordinateIndices.append(j)
                        j += 1
                    textureCoordinateIndices.append(-1)

                texCoordIndices = ", ".join(map(str, textureCoordinateIndices))
                indexedFaceSet.setAttribute("texCoordIndex", texCoordIndices)

                textureCoordinate = self.xel("TextureCoordinate")
                textureCoordinate.setAttribute("point", ", ".join(textureCoordinates))
                indexedFaceSet.appendChild(textureCoordinate)

                # FIXME: Only write last imageTexture created, we only need the last
                # as long as we don't use multiple images.
                appearance.appendChild(imageTextures[0])

            else:
                raise RuntimeError("Object %s has use_face_texture but no active textures" % ob.name)

        # Smoothing data is stored in faces, not the object itself
        #if any([f.use_smooth for f in ob.data.faces]):
            #indexedFaceSet.setAttribute("creaseAngle", str(ob.data.auto_smooth_angle * DEG2RAD))
        if any([f.use_smooth for f in mesh.faces]):
            indexedFaceSet.setAttribute("creaseAngle", self.strfloat(mesh.auto_smooth_angle * DEG2RAD))

        if mesh.show_double_sided:
            indexedFaceSet.setAttribute("solid", "false")

        # Build coordIndex
        faces = []
        for face in mesh.faces:
            if len(face.vertices) == 3:
                faces.append("%i %i %i -1" % tuple(face.vertices))
            else:
                faces.append("%i %i %i %i -1" % tuple(face.vertices))
        indexedFaceSet.setAttribute("coordIndex", ', '.join(faces))

        # Build Coordinate
        coordinate = self.xel("Coordinate")

        # Use existing mesh data if it's available
        cname = "Coord_" + ob.data.name
        if cname in self._def_names:
            coordinate.setAttribute("USE", cname)
        else:
            # NOTE: We're passing ob.data instead of ob to create_def_name
            # to obtain the mesh data name for the coordinates.
            coordinate.setAttribute("DEF", self.create_def_name(ob.data, "Coord"))
            points = []
            for v in mesh.vertices:
                points.append("%.6f %.6f %.6f" % tuple(v.co))
            coordinate.setAttribute("point", ', '.join(points))
        indexedFaceSet.appendChild(coordinate)

        if "hgt_fallthroughProtect" in ob:
            hapticsOptions = self.xel("HapticsOptions")
            hapticsOptions.setAttribute("maxDistance", "0.04")
            indexedFaceSet.appendChild(hapticsOptions)

        return el

    def render_text(self, ob):
        el = self.render_transform(ob)
        shape = self.xel("Shape")
        el.appendChild(shape)

        material = self.render_material(ob)
        appearance = self.xel("Appearance")
        appearance.setAttribute("DEF", self.create_def_name(ob, "Appearance"))
        appearance.appendChild(material)
        shape.appendChild(appearance)

        # Look in object's custom properties for haptic surface
        if "FS" in ob:
            frictionalSurface = self.xel("FrictionalSurface")
            appearance.appendChild(frictionalSurface)
        if "SS" in ob:
            smoothSurface = self.xel("SmoothSurface")
            appearance.appendChild(smoothSurface)

        text = self.xel("Text")
        text.setAttribute("DEF", self.create_def_name(ob, "Text"))

        # FIXME: in order for lines to render properly, it seems as if
        # this format needs to be used: string='"line1" "line2"'
        # See if delimiters can be changed in minidom.
        lines = ob.data.body.split("\n")
        if len(lines) > 1:
            raise RuntimeError("Multi-line Text is not supported.")
        line_string = " ".join(["%s" % line for line in lines])
        text.setAttribute("string", line_string)

        fontstyle = self.xel("FontStyle")
        # Use Droid Sans as default font
        fontname = ob.data.font.name
        if fontname == "Bfont":
            fontname = "Droid Sans"
        fontstyle.setAttribute("family", fontname)
        fontstyle.setAttribute("size", self.strfloat(ob.data.size))
        justifications = {
            "LEFT": "BEGIN",
            "CENTER": "MIDDLE",
            "RIGHT": "END",
        }
        fontstyle.setAttribute("justify", justifications[ob.data.align])

        if "hgt_renderType" in ob.data:
            fontstyle.setAttribute("renderType", "POLYGON")

        text.appendChild(fontstyle)
        shape.appendChild(text)

        return el

    # Special case #1:
    # An empty is mapped to a node composed of a ToggleGroup
    # and an inner Transform. Also includes a TransformInfo.
    # If the property hgt_DynamicTransform is set (to anything),
    # a DynamicTransform is set as the "bottom" node of the
    # empty.

    # Modification: all transforms are now rendered as empties, including
    # TransformInfo, ToggleGroup and optional DynamicTransform

    def render_transform(self, ob):
        print("Render Transform %s" % ob.name)
        return self.render_empty(ob)

    def render_empty(self, ob):
        if 'sortorder' in ob:
            print("Render Empty %s, sortorder %f" % (ob.name, ob['sortorder']))
        else:
            print("Render Empty %s" % (ob.name))

        toggle = self.xel("ToggleGroup")

        toggle.setAttribute("DEF", self.create_def_name(ob, "ToggleGroup"))

        transform = self.xel("Transform")
        transform.setAttribute("DEF", self.create_def_name(ob, "Transform"))
        m = ob.matrix_local
        t = m.to_translation()
        r = m.to_quaternion()
        ra = r.axis
        s = m.to_scale()
        transform.setAttribute("translation", "%f %f %f" % tuple(t))
        transform.setAttribute("scale", "%f %f %f" % tuple(s))
        transform.setAttribute("rotation", "%f %f %f %f" % (ra[0], ra[1], ra[2], r.angle))

        # Append a TransformInfo to be able to retrieve
        # forward and inverse matrices from the location
        # of the empty.
        transformInfo = self.xel("TransformInfo")
        transformInfo.setAttribute("DEF", self.create_def_name(ob, "TransformInfo"))
        toggle.appendChild(transformInfo)

        # Look for special flags (blender object properties)
        # FIXME: currently flags are mutually exclusice (see below)
        #
        # Let's go ahead and modify the element's appendChild method
        # so that elements are appended to the child node instead.

        if "hgt_DynamicTransform" in ob:
            dynamic_transform = self.xel("DynamicTransform")
            dynamic_transform.setAttribute("DEF", self.create_def_name(ob, "DynamicTransform"))
            toggle.appendChild(transform)
            transform.appendChild(dynamic_transform)
            toggle.appendChild = dynamic_transform.appendChild
        elif "hgt_Billboard" in ob:
            billboard = self.xel("Billboard")
            billboard.setAttribute("axisOfRotation", "1 0 0")
            toggle.appendChild(transform)
            transform.appendChild(billboard)
            toggle.appendChild = billboard.appendChild
        else:
            # Default behavior
            toggle.appendChild(transform)
            toggle.appendChild = transform.appendChild

        return toggle

    def render_background(self):
        # Background node
        bgt = self.xel("Transform")
        bgt.setAttribute("rotation", "1 0 0 %.6f" % (90 * DEG2RAD))

        hor = self.scene.world.horizon_color
        hor_str = self.color_string(tuple(hor))
        bg = self.xel("Background")

        # Not handled correctly
        if self.scene.world.use_sky_blend:
            zen = self.scene.world.zenith_color
            zen_str = self.color_string(tuple(zen))
            blend_str = self.color_string((
                (hor[0] + zen[0]) / 2.0,
                (hor[1] + zen[1]) / 2.0,
                (hor[2] + zen[2]) / 2.0,
            ))
            if self.scene.world.use_sky_real:
                bg.setAttribute("groundColor", "%s, %s, %s" % (zen_str, blend_str, hor_str))
                bg.setAttribute("skyColor", "%s, %s, %s" % (zen_str, blend_str, hor_str))
                bg.setAttribute("groundAngle", "%f, %f" % (45 * DEG2RAD, 90 * DEG2RAD))
                bg.setAttribute("skyAngle", "%f, %f" % (45 * DEG2RAD, 90 * DEG2RAD))
            else:
                bg.setAttribute("groundColor", "%s, %s" % (hor_str, blend_str))
                bg.setAttribute("skyColor", "%s, %s" % (zen_str, blend_str))
                bg.setAttribute("groundAngle", self.strfloat(90 * DEG2RAD))
                bg.setAttribute("skyAngle", self.strfloat(90 * DEG2RAD))
        # Single sky color handled correctly
        else:
            zen = self.scene.world.horizon_color
            zen_str = self.color_string(tuple(zen))
            bg.setAttribute("groundColor", self.color_string(tuple(hor)))
            bg.setAttribute("skyColor", self.color_string(tuple(zen)))

        bgt.appendChild(bg)
        return bgt

    def render_image_texture(self, tex):
        imageTexture = self.xel("ImageTexture")
        imagename = tex.image.name
        if imagename in self._imagetextures:
            imageTexture.setAttribute("USE", "ImageTexture_" + imagename) # FIXME
        else:
            self._imagetextures[imagename] = imagename
            imageTexture.setAttribute("DEF", self.create_def_name(tex.image, 'ImageTexture')) # FIXME
            imagepath = tex.image.filepath.split('//')[-1].replace('\\', '/')
            imageTexture.setAttribute("url", imagepath)

        return imageTexture

    def render_material(self, ob):
        m = self.xel("Material")
        oms = ob.data.materials
        if len(oms) == 1:
            om = oms[0]
            if om in self._materials:
                # TODO: use a method instead of hardcoding, when create_def_name has matured
                m.setAttribute("USE", "Material_" + om.name)
            else:
                self._materials[om] = om
                m.setAttribute("DEF", self.create_def_name(om, 'Material'))
                m.setAttribute("diffuseColor", self.color_string(tuple(om.diffuse_color), multiplier = om.diffuse_intensity))
                m.setAttribute("specularColor", self.color_string(tuple(om.specular_color), multiplier = om.specular_intensity))
                m.setAttribute("emissiveColor", self.color_string(tuple(om.diffuse_color), multiplier = om.emit * om.diffuse_intensity))
                m.setAttribute("shininess", self.strfloat(om.specular_hardness / 512.0))
                if om.use_transparency:
                    m.setAttribute("transparency", self.strfloat(1.0 - om.alpha))
                m.setAttribute("ambientIntensity", self.strfloat(om.ambient))
        else:
            raise RuntimeError("Object %s has %d material(s). Objects must have one and only one material." % (ob.name, len(oms)))
        return m

    # Helper functions
    def create_def_name(self, ob, prefix):
        n = prefix + "_" + ob.name
        if n in self._def_names:
            raise RuntimeError("Object name (%s) already in _def_names" % n)
        else:
            self._def_names[n] = ob
            #print("\t" + n)
            return n

    def xel(self, name):
        return self.xml.createElement(name)

    def color_string(self, values, multiplier=1.0):
        vs = [self.color_correct(v * multiplier) for v in values]
        s = "%.6f %.6f %.6f" % tuple(vs) # rounding didn't really achieve anything, since we're hardcoding here
        return s

    # Convert a float to a str
    def strfloat(self, f):
        return str(round(f, DECIMAL_PRECISION))

    # Convert single color from linear space to sRGB if scene
    # has color management enabled.
    # http://www.blender.org/development/release-logs/blender-256-beta/color-management/
    # http://en.wikipedia.org/wiki/SRGB_color_space
    def color_correct(self, linearColor):
        if self.scene.render.use_color_management:
            climit = 0.0031308
            a = 0.055
            b = 1.0 / 2.4
            if linearColor <= climit:
                cRGB = 12.92 * linearColor
            else:
                cRGB = ((1 + a) * (linearColor ** b)) - a

            assert(cRGB >= 0.0 and cRGB <= 1.0)

            return cRGB
        else:
            return linearColor

###########################################################################
# A node-like container for Blender objects.
###########################################################################
class ObjectContainer:
    def __init__(self, ob):
        self.object = ob
        self.children = []
        if 'sortorder' in ob:
            self.sortorder = float(ob['sortorder'])
        else:
            self.sortorder = 0.5

    def add_child(self, oc):
        self.children.append(oc)

###########################################################################
# A tree of ObjectContainers, representing Blender's parenting structure.
###########################################################################
class Tree:
    def __init__(self, context):
        self.context = context
        self.root = []
        self.objects = {}
        self.objectContainers = {}

        self.collect_tree()
        self.create_tree()

        self.root = sorted(self.root, key=lambda oc: oc.sortorder)

    def collect_tree(self):
        objectList = self.context.visible_objects
        for ob in objectList:
            if ob.name not in self.objects:
                self.objects[ob.name] = ob
                oc = ObjectContainer(ob)
                self.objectContainers[ob] = oc
            else:
                raise RuntimeError("Duplicate object name: %s" % (ob.name))

    def create_tree(self):
        for ob in self.objects.values():
            parent = ob.parent
            oc = self.objectContainers[ob]
            if parent is None:
                self.root.append(oc)
            else:
                self.objectContainers[parent].add_child(oc)

###########################################################################
# Save mechanism, initiated by forces unkown yonder.
###########################################################################
def save(operator, context, **properties):
    filepath = properties['filepath']
    if not filepath.lower().endswith('.hgt'):
        filepath = '.'.join(filepath.split('.')[:-1]) + '.hgt'
    pyfilepath = '.'.join(filepath.split('.')[:-1]) + '.py'

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")

    exporter = HGTExporter(
        context = context,
        filepath = filepath,
        pyfilepath = pyfilepath,
        options = properties,
    )
    exporter.export()

    bpy.ops.object.select_all(action="DESELECT")

    # Save the blender file if the export didn't raise an exception,
    # unless we're testing.
    if properties["nosave"]:
        print("Not saving .blend file")
    else:
        bpy.ops.wm.save_mainfile()
    print("*** HGT Exporter finished. ***\n")

    return {'FINISHED'}

