# -*- Mode: Python -*-
# -*- coding: ascii -*-

"""
This is a LightWave Command Sequence plug-in (Modeler) that copies
selected layers into a new object.
"""

import os
import re
import sys
import lwsdk

__author__     = "Alexander Sokolov"
__date__       = "Feb 20 2025"
__copyright__  = "copyright (C) 2024 Alexander Sokolov"
__version__    = "1.0"
__maintainer__ = "Alexander Sokolov"
__email__      = "zmechanic@gmail.com"
__status__     = "Example"
__lwver__      = "2018"

class assemble_layers(lwsdk.ICommandSequence):
    def __init__(self, context):
        super(assemble_layers, self).__init__()
        
    # Presents an info message to the user.
    def info(self, title, message):
        lwsdk.LWMessageFuncs().info(title, message)
        
    # Presents an info message to the user.
    def error(self, title, message):
        lwsdk.LWMessageFuncs().error(title, message)
       
    # Asks user to enter some text.
    def ask_name(self, title, name, default_value):
        return lwsdk.LWMessageFuncs().askName(title, name, default_value)

    # Asks user to make a choice.
    def ask_ok_cancel(self, title, message, extra_message):
        return lwsdk.LWMessageFuncs().okCancel(title, message, extra_message)

    # Asks user to make a choice.
    def ask_yes_no(self, title, message, extra_message):
        return lwsdk.LWMessageFuncs().yesNo(title, message, extra_message)

    # Asks user to make a choice.
    def ask_yes_no_cancel(self, title, message, extra_message):
        return lwsdk.LWMessageFuncs().yesNoCan(title, message, extra_message)
        
    def get_commands(self):
        command_list = {}
        for command in ["SETOBJECT",
                        "SETLAYER",
                        "SETBLAYER",
                        "SEL_POINT",
                        "DELETE",
                        "COPY",
                        "PASTE",
                        "BOOLEAN"]:
            command_list[command] = mod_command.lookup(mod_command.data, command)
        return command_list
        
    def execute(self, command, options=None):
        cs_options = None if options is None else lwsdk.marshall_dynavalues(options)
        return mod_command.execute(mod_command.data, command, cs_options, lwsdk.OPSEL_USER)
        
    def select_object(self, object_name):
        self.execute(command_lookup["SETOBJECT"], str(object_name))
        
    # Activates FOREground layer. Index is 1-based, not 0-based.
    def select_fg_layer(self, layer_str_index):
        self.execute(command_lookup["SETLAYER"], str(layer_str_index))

    # Activates BACKground layer. Index is 1-based, not 0-based.
    def select_bg_layer(self, layer_str_index):
        self.execute(command_lookup["SETBLAYER"], str(layer_str_index))
        
    # Deletes content from layer
    def clear_layer(self, layer_id):
        self.select_fg_layer(layer_id)
        self.execute(command_lookup["DELETE"])

    # Copies content from one layer to another
    def copy_layer_to_layer(self, src_layer_id, dst_layer_id):
        self.select_fg_layer(src_layer_id)
        self.execute(command_lookup["COPY"])
        self.select_fg_layer(dst_layer_id)
        self.execute(command_lookup["PASTE"])

    def substract_layer_from_layer(self, src_layer_id, dst_layer_id):
        self.select_fg_layer(dst_layer_id)
        self.select_bg_layer(src_layer_id)
        self.execute(command_lookup["BOOLEAN"], "SUBTRACT")
        
    def process_steps(self, step, sub_steps_keys, layer_name_to_index, part_target_layer):
        # Clear target layer
        self.clear_layer(part_target_layer)

        for sub_part_num in range(1, 100):
            sub_step = '{}.{}'.format(step, sub_part_num)
            
            has_sub_sub_steps = any(i.startswith(sub_step + ".") for i in sub_steps_keys)
            if has_sub_sub_steps:
                sub_part_layer = layer_name_to_index.get(sub_step)
                if not sub_part_layer:
                    self.error('Cannot locate target build layer for part {}.'.format(sub_step), 'You need to include "{{{}}}" into the name of the layer that will be the target for your part build.'.format(sub_step))
                    break
                self.process_steps(sub_step, sub_steps_keys, layer_name_to_index, sub_part_layer)
            
            op_mov = sub_step in sub_steps_keys
            op_sub = (sub_step + '-') in sub_steps_keys
            if op_mov:
                sub_part_layer = layer_name_to_index.get(sub_step)
                if not sub_part_layer:
                    self.error('Cannot locate source layer {} for part {}.'.format(sub_step, step), None)
                    break
                self.copy_layer_to_layer(sub_part_layer, part_target_layer)
            elif op_sub:
                sub_part_layer = layer_name_to_index.get(sub_step + '-')
                if not sub_part_layer:
                    self.error('Cannot locate source layer {} for part {}.'.format(sub_step, step), None)
                    break
                self.substract_layer_from_layer(sub_part_layer, part_target_layer)

    def process(self, mod):
        global mod_command, command_lookup
        mod_command = mod
        command_lookup = self.get_commands()

        state_query = lwsdk.LWStateQueryFuncs()
        obj_funcs = lwsdk.LWObjectFuncs()
        
        # Get the OS specific separators
        separator = os.sep
        
        # Get file name
        obj = state_query.object()
        obj_fullname = obj.split(separator)
        obj_name = obj_fullname[len(obj_fullname)-1][:-4]
        
        #get starting object id
        object_index = 0
        for count in range(obj_funcs.numObjects()):
           if obj_funcs.userName(object_index) is obj_name:
                object_index = count
                break
                
        layers_raw = state_query.layerList(lwsdk.OPLYR_ALL, obj_name).split(" ") #'OPLYR_ALL', 'OPLYR_BG', 'OPLYR_EMPTY', 'OPLYR_FG', 'OPLYR_NONEMPTY', 'OPLYR_PRIMARY', 'OPLYR_SELECT'
        available_layers = [l for l in layers_raw if l.strip()]
        
        # https://documentation.help/LightWave/me.html
        # mesh_edit_op = mod_command.editBegin(0, 0, lwsdk.OPSEL_USER)
        # if not mesh_edit_op:
            # self.info("Failed to engage mesh edit operations!", None)
            # return lwsdk.AFUNC_OK
            
        # oplayer = 0
        # npoints = mesh_edit_op.pointCount(mesh_edit_op.state, oplayer, lwsdk.EDCOUNT_SELECT)
        # npolygons = mesh_edit_op.polyCount(mesh_edit_op.state, oplayer, lwsdk.EDCOUNT_SELECT)
        
        # edit_op_result = lwsdk.EDERR_USERABORT
        # #edit_op_result = lwsdk.EDERR_NONE
        # mesh_edit_op.done(mesh_edit_op.state, edit_op_result, 0)
        
        # self.info("DONE", None)
        # return lwsdk.AFUNC_OK
        
        layer_name_to_index = {}
        
        # Iterate through all non-blank layers
        for layer_str_index in available_layers:
            # Layer numerical index that's accepted by Python methods (not execute command) are zero 0 based
            layer_num_index = int(layer_str_index) - 1
            
            # Skip non-existent layers
            if not obj_funcs.layerExists(object_index, layer_num_index):
                continue
        
            # Get layer visibility, and skip hidden layers
            is_layer_visible = obj_funcs.layerVis(object_index, layer_num_index)
            if not is_layer_visible:
                continue

            # #print(dir(lwsdk.pcore.LWMeshInfo))
            # layer_mesh = obj_funcs.layerMesh(object_index, layer_num_index)

            # # Get number of polygons on the layer and skip empty layer
            # num_polys = layer_mesh.numPolygons()
            # if num_polys == 0:
                # continue

            # Get layer name, and skip if layer have no name
            layer_name = obj_funcs.layerName(object_index, layer_num_index)
            if not layer_name:
                continue

            # Obtain content inside of curly brackets, and skip if none
            instructions = re.findall(r'\{([^}]+)\}', layer_name)
            if not instructions:
                continue

            for instruction in instructions:
                tokens = [token.strip() for token in instruction.split(";") if token.strip()]
                for token in tokens:
                    layer_name_to_index[token] = layer_str_index;

            # iterator = layer_mesh.createMeshIterator(lwsdk.LWMESHITER_POLYGON)
            # count = 0
            # while count < num_polys:
                # poly_id = layer_mesh.iterateMesh(iterator)
                # print(layer_mesh.polFlags(poly_id))
                # count += 1

            # layer_mesh.destroyMeshIterator(iterator)

            #self.select_object(obj_name)
            #self.select_fg_layer(layer_str_index)
        
        # Iterate through possible part numbers
        for part_num in range(1, 100):
            step = str(part_num)
            sub_steps_keys = [key for key in layer_name_to_index.keys() if key.startswith(step + ".")]
            
            # Skip if we got less than one sub-step to include in the build
            if len(sub_steps_keys) == 0:
                continue
            
            # Try to obtain final part target layer, if assigned
            part_target_layer = layer_name_to_index.get(step)
            if not part_target_layer:
                self.error('Cannot locate target build layer for part {}.'.format(step), 'You need to include "{{{}}}" into the name of the layer that will be the target for your part build.'.format(step))
                break

            # Run steps
            self.process_steps(step, sub_steps_keys, layer_name_to_index, part_target_layer)

        self.info("Parts created", None)
        return lwsdk.AFUNC_OK

ServerTagInfo = [
                    ( "Python Assemble Layers", lwsdk.SRVTAG_USERNAME | lwsdk.LANGID_USENGLISH ),
                    ( "Assemble Layers as LWO", lwsdk.SRVTAG_BUTTONNAME | lwsdk.LANGID_USENGLISH ),
                    ( "Utilities/Python", lwsdk.SRVTAG_MENU | lwsdk.LANGID_USENGLISH )
                ]

ServerRecord = { lwsdk.CommandSequenceFactory("LW_PyAssembleLayers", assemble_layers) : ServerTagInfo }

#http://www.etwright.org/lwsdk/docs/classes/me.html#eltopselect
#https://clintons3d.com/plugins/downloads/square2.py
#https://github.com/heimlich1024/OD_CopyPasteExternal/tree/master/Lightwave
#https://documentation.help/LightWave/w2s.html