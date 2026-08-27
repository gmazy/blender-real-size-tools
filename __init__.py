bl_info = {  
    "name": "Real Size Tools",  
    "author": "Mazay",  
    "version": (2026, 2, 3),
    "blender": (2, 80, 0),  
    "location": "View > Viewpoint, Empty > Image",  
    "description": "Set viewport to actual real life scale, load reference images in scale.",  
    "warning": "",  
    "doc_url": "https://github.com/gmazy/blender-real-size-tools",  
    "tracker_url": "https://github.com/gmazy/blender-real-size-tools/issues",  
    "category": "3D View"}

import bpy
import math
import numpy
from bpy.props import IntProperty, FloatProperty, BoolProperty

class real_size_tools(bpy.types.AddonPreferences):
    bl_idname = __name__

    screen_dpi : FloatProperty(
        name="Screen DPI",
        description="Type your display DPI from display manual",
        default=95,
        soft_min=1,
        )

    units_are_mm : BoolProperty(
        name="Use scale instead of real size",
        description="Scale will be applied on top of real size when this is enabled\n"
                    "and Blender's Unit Scale is left at it's default value",
        default=False,
        )

    extra_scale : FloatProperty(
        name="Scale 1:x",
        description="Scale 1:x",
        default=1000,
        soft_min=1,
        )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "screen_dpi")
        layout.separator()
        layout.prop(self, "units_are_mm")
        if self.units_are_mm:
            layout.prop(self, "extra_scale")
            if self.extra_scale != 1:
                scale_format = prefs.scale_str()
                if bpy.context.scene.unit_settings.scale_length != 1: #
                    layout.label(text="Scale disabled, please set Blender's unit scale to 1")
                else:
                    layout.label(text="This enables view scale of 1:"+scale_format+
                                      " and image/empty scale of "+scale_format)


class RealSizeView(bpy.types.Operator):
    """View in real size"""
    bl_idname = "view3d.real_size_view"
    bl_label = "View in Actual Size"
    bl_options = {'REGISTER', 'UNDO'}

    screen_dpi : FloatProperty(
        name="Screen DPI",
        description="Screen DPI for current operation",
        default=0,
        soft_min=0,
        step=10,
        options={'SKIP_SAVE'})
    save_screen_dpi : BoolProperty(
        name="Set as default",
        description="Save DPI as the new default changing addon preferences",
        default=False,
        options={'SKIP_SAVE'})
    scale : FloatProperty(
        name="Scale 1:x",
        description="Set value of this to 2 to use 1:2 scale",
        default=0,
        soft_min=1,
        soft_max=1000,
        step=10,
        precision=1,
        options={'SKIP_SAVE'})

    def execute(self, context):
        preferences = bpy.context.preferences.addons[__name__].preferences
        unit_scale = context.scene.unit_settings.scale_length

         # Setting DPI to 0 uses value from preferences.
        if self.screen_dpi == 0:
            self.screen_dpi = preferences.screen_dpi

        # Setting Scale to 0 uses default scale.
        if self.scale == 0:
            self.scale = prefs.scale()

        # Update addon preferences with checked checkbox
        if self.save_screen_dpi:
            preferences.screen_dpi = self.screen_dpi

        area = next(area for area in bpy.context.screen.areas if area.type == "VIEW_3D")

        # Switch to ortographic
        region_3d = area.spaces.active.region_3d
        if region_3d.view_perspective == 'PERSP':
            with bpy.context.temp_override(area=area, region=area.regions[-1]):
                bpy.ops.view3d.view_axis(type='FRONT')   

        # Set view in DPI
        screen_dpm = self.screen_dpi / 25.4 * 1000 # Pixels per screen m
        scene_dpm = area.width / 1.44 # Pixels per scene m
        region_3d.view_distance = scene_dpm / screen_dpm / unit_scale * self.scale
        return {'FINISHED'}

class prefs():
    def scale():
        unit_scale = bpy.context.scene.unit_settings.scale_length
        preferences = bpy.context.preferences.addons[__name__].preferences
        if preferences.units_are_mm and unit_scale == 1:
            return preferences.extra_scale
        return 1

    @classmethod
    def scale_xyz(cls):
        scale = cls.scale()
        return (scale,scale,scale)

    @classmethod
    def scale_str(cls):
        scale = str(round(cls.scale(),3))
        return scale.rstrip('0').rstrip('.') if '.' in scale else scale

class RealSizeImageEmpty(bpy.types.Operator):
    """Set image to it's actual size based on image metadata"""
    bl_idname = "view3d.real_size_image_empty" #VIEW3D_OT_real_size_image_viewer
    bl_label = "View in Actual Size"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def calc_display_size(cls, img):
        unit_scale = bpy.context.scene.unit_settings.scale_length
        display_size = max(img.size) / max(img.resolution) / unit_scale
        return display_size * prefs.scale()

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
            scale = prefs.scale()
            display_size = cls.calc_display_size(obj.data)
            if (numpy.float32(obj.empty_display_size) != numpy.float32(display_size) or
                tuple(obj.scale) != scale):
                return True
        return False

    def execute(self, context):
        obj = context.object
        obj.empty_display_size = self.calc_display_size(obj.data)
        obj.scale = prefs.scale_xyz()
        return {'FINISHED'}

class RealSizeImageViewer(bpy.types.Operator):
    """Set image to it's actual size based on image metadata"""
    bl_idname = "image.view_zoom_real_size" 
    bl_label = "View in Actual Size"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        # Find open image ditor. This may fail if multiple editors are open.
        area = False
        for area in bpy.context.screen.areas :
            if area.type == 'IMAGE_EDITOR' or area.type == 'UV_EDITOR':
                break
        # Find image
        if area and area.spaces.active.image:
            img = area.spaces.active.image

            # Find dpi ratio
            image_dpi = max(img.resolution) * 0.0254
            screen_dpi = bpy.context.preferences.addons[__name__].preferences.screen_dpi
            ratio = screen_dpi / image_dpi

            # Change view zoom
            bpy.ops.image.view_zoom_ratio(ratio=ratio)
        return {'FINISHED'}


def menu_func_view(self, context):
    self.layout.separator()
    op_text = "View in Actual Size"
    scale = prefs.scale_str()
    if scale != "1":
        op_text += " (1:" + scale + ")"
    self.layout.operator(RealSizeView.bl_idname, text=op_text)

def menu_func_image_empty(self, context):
    obj = context.object
    if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
        dpi = max(obj.data.size) / obj.empty_display_size * 0.0254 / context.scene.unit_settings.scale_length

        layout = self.layout
        layout.label(text="DPI: "+str(round(dpi,2)))

        op_text = "View in Actual Size"
        scale = prefs.scale_str()
        if scale != "1":
            op_text += " x " + scale
        layout.operator(RealSizeImageEmpty.bl_idname, text=op_text)

def menu_func_image_viewer(self, context):
    obj = context.object
    self.layout.separator()
    self.layout.operator(RealSizeImageViewer.bl_idname)


def register():
    bpy.utils.register_class(RealSizeView)
    bpy.utils.register_class(RealSizeImageEmpty)
    bpy.utils.register_class(RealSizeImageViewer)
    bpy.utils.register_class(real_size_tools)
    bpy.types.VIEW3D_MT_view_viewpoint.append(menu_func_view)
    bpy.types.DATA_PT_empty.append(menu_func_image_empty)
    bpy.types.IMAGE_MT_view_zoom.append(menu_func_image_viewer)


def unregister():
    bpy.utils.unregister_class(RealSizeView)
    bpy.utils.unregister_class(RealSizeImageEmpty)
    bpy.utils.unregister_class(RealSizeImageViewer)
    bpy.utils.unregister_class(real_size_tools)
    bpy.types.VIEW3D_MT_view_viewpoint.remove(menu_func_view)
    bpy.types.DATA_PT_empty.remove(menu_func_image_empty)
    bpy.types.IMAGE_MT_view_zoom.remove(menu_func_image_viewer)


if __name__ == "__main__":
    register()