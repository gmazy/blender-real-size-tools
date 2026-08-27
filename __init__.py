bl_info = {  
    "name": "Real Size Tools",  
    "author": "Mazay",  
    "version": (0, 1, 0),
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
        description="\nType your display DPI from display manual",
        default=95,
        )

    units_are_mm : BoolProperty(
        name="Treat default unit as millimeter",
        description="1000x scale will be applied when this is enabled and "
                    "Blender's Unit Scale is left at it's default value.\n"
                    "Note: Blender restart may be required for view scale change.",
        default=False,
        )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "screen_dpi")
        layout.separator()
        layout.label(text="3D Printing Specials:")
        layout.prop(self, "units_are_mm")

class RealSizeView(bpy.types.Operator):
    """View in real size using display DPI from Real Size Tools addon's preferences"""
    bl_idname = "view3d.real_size_view"
    bl_label = "View in Actual Size"
    bl_options = {'REGISTER', 'UNDO'}

    screen_dpi : FloatProperty(
        name="Screen DPI",
        description="Screen DPI for current operation. ",
        default=0)
    save_screen_dpi : BoolProperty(
        name="Set as default",
        description="Save DPI as the new default changing addon preferences",
        default=False)
    scale : FloatProperty(
        name="Scale 1:x",
        description="Set value of this to 2 to use 1:2 scale.",
        precision=0,
        default=0)


    def execute(self, context):
        preferences = bpy.context.preferences.addons[__name__].preferences
        unit_scale = context.scene.unit_settings.scale_length

         # Setting DPI to 0 uses value from preferences.
        if self.screen_dpi == 0:
            self.screen_dpi = preferences.screen_dpi

        # Setting Scale to 0 uses default scale.
        if self.scale == 0 and preferences.units_are_mm and unit_scale == 1:
            self.scale = 1000
        elif self.scale == 0:
            self.scale = 1

        # Update addon preferences with enabled checkbox
        if self.save_screen_dpi:
            preferences.screen_dpi = self.screen_dpi

        area = next(area for area in bpy.context.screen.areas if area.type == "VIEW_3D")
        with bpy.context.temp_override(area=area, region=area.regions[-1]):
            bpy.ops.view3d.view_axis(type='FRONT')     
        region_3d = area.spaces.active.region_3d

        region_3d.view_distance = area.width / self.screen_dpi * 0.01753 * self.scale / unit_scale
        return {'FINISHED'}

class RealSizeImage(bpy.types.Operator):
    """Set image to it's actual size based on image metadata"""
    bl_idname = "view3d.real_size_image" #VIEW3D_OT_real_size_image
    bl_label = "View in Actual Size"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def calc_display_size(cls, img):
        unit_scale = bpy.context.scene.unit_settings.scale_length
        units_are_mm = bpy.context.preferences.addons[__name__].preferences.units_are_mm
        display_size = max(img.size) / max(img.resolution) / unit_scale
        if unit_scale == 1 and units_are_mm:
            display_size = display_size / 0.001
        return display_size

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
            display_size = cls.calc_display_size(obj.data)
            if numpy.float32(obj.empty_display_size) != numpy.float32(display_size):
                return True
        return False

    def execute(self, context):
        obj = context.object
        obj.empty_display_size = self.calc_display_size(obj.data)
        return {'FINISHED'}

def menu_func_view(self, context):
    self.layout.separator()
    op_text = "View in Actual Size"
    if (context.preferences.addons[__name__].preferences.units_are_mm and
        context.scene.unit_settings.scale_length == 1):
        op_text += " (1:1000)"
    self.layout.operator(RealSizeView.bl_idname, text=op_text)

def menu_func_image(self, context):
    obj = context.object
    if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
        dpi = max(obj.data.size) / obj.empty_display_size * 0.0254 / context.scene.unit_settings.scale_length

        layout = self.layout
        layout.label(text="DPI: "+str(round(dpi,2)))

        op_text = "View in Actual Size"
        if (context.preferences.addons[__name__].preferences.units_are_mm and
            context.scene.unit_settings.scale_length == 1):
            op_text += " x 1000"
        layout.operator(RealSizeImage.bl_idname, text=op_text)



def register():
    bpy.utils.register_class(RealSizeView)
    bpy.utils.register_class(RealSizeImage)
    bpy.utils.register_class(real_size_tools)
    bpy.types.VIEW3D_MT_view_viewpoint.append(menu_func_view)
    bpy.types.DATA_PT_empty.append(menu_func_image)


def unregister():
    bpy.utils.unregister_class(RealSizeView)
    bpy.utils.unregister_class(RealSizeImage)
    bpy.utils.unregister_class(real_size_tools)
    bpy.types.VIEW3D_MT_view_viewpoint.remove(menu_func_view)
    bpy.types.DATA_PT_empty.remove(menu_func_image)


if __name__ == "__main__":
    register()