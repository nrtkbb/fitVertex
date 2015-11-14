# -*- coding: utf-8 -*
"""
import maya.cmds
maya.cmds.loadPlugin("fitvertex.py")
maya.cmds.fitVertex()
"""

import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx


class FitVertexCmd(OpenMayaMPx.MPxCommand):
    kPluginCmdName = "fitVertex"
    selection_error = ValueError(u'Please select two mesh.')

    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)
        self.first_meshfn = None
        self.first_vertex_list = None
        self.first_points = None
        self.second_points = None
        self.nearest_list = None

    @staticmethod
    def cmd_creator():
        return OpenMayaMPx.asMPxPtr(FitVertexCmd())

    def doIt(self, *args, **kwargs):
        selection = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.getActiveSelectionList(selection)

        if not FitVertexCmd.selection_check(selection):
            raise FitVertexCmd.selection_error

        self.first_meshfn, self.first_vertex_list, self.first_points = FitVertexCmd.get_variables(0, selection)
        self.second_points = FitVertexCmd.get_points(1, selection)

        self.nearest_list = OpenMaya.MPointArray(self.first_meshfn.numVertices())
        for first_vertex in self.first_vertex_list:
            nearest = FitVertexCmd.get_nearest(self.first_points[first_vertex], self.second_points)
            self.nearest_list.set(nearest, first_vertex)
        self.redoIt()

    def redoIt(self, *args, **kwargs):
        for first_vertex in self.first_vertex_list:
            self.first_meshfn.setPoint(first_vertex, self.nearest_list[first_vertex], OpenMaya.MSpace.kWorld)

    def undoIt(self, *args, **kwargs):
        for first_vertex in self.first_vertex_list:
            self.first_meshfn.setPoint(first_vertex, self.first_points[first_vertex], OpenMaya.MSpace.kWorld)

    def isUndoable(self, *args, **kwargs):
        return True

    @staticmethod
    def selection_check(selection):
        """
        :param selection: OpenMaya.MSelectionList
        :rtype bool
        """
        if selection.length() is not 2:
            sys.stdout.write("Failed to selection length is not 2.\n")
            return False

        meshfn = OpenMaya.MFnMesh()
        node = OpenMaya.MDagPath()
        itr = OpenMaya.MItSelectionList(selection)
        while 0 == itr.isDone():
            itr.getDagPath(node)
            meshfn.setObject(node)
            if not meshfn:
                sys.stdout.write("Failed to selection type is not mesh [%s].\n" % meshfn.name())
                return False
            itr.next()

        return True

    @staticmethod
    def get_variables(index, selection):
        """
        :param index: int
        :param selection: OpenMaya.MSelectionList
        :rtype : OpenMaya.MFnMesh, OpenMaya.MIntArray, OpenMaya.MPointArray
        """
        node = OpenMaya.MDagPath()
        component = OpenMaya.MObject()
        selection.getDagPath(index, node, component)
        meshfn = OpenMaya.MFnMesh(node)
        vertex_count = OpenMaya.MIntArray()
        vertex_list = OpenMaya.MIntArray()
        meshfn.getVertices(vertex_count, vertex_list)
        points = OpenMaya.MPointArray(meshfn.numVertices())
        for vertex in vertex_list:
            point = OpenMaya.MPoint()
            meshfn.getPoint(vertex, point, OpenMaya.MSpace.kWorld)
            points.set(point, vertex)
        return meshfn, vertex_list, points

    @staticmethod
    def get_points(index, selection):
        """
        :param index: int
        :param selection: OpenMaya.MSelectionList
        :return: OpenMaya.MPointArray
        """
        node = OpenMaya.MDagPath()
        component = OpenMaya.MObject()
        selection.getDagPath(index, node, component)
        meshfn = OpenMaya.MFnMesh(node)
        points = OpenMaya.MPointArray(meshfn.numVertices())
        meshfn.getPoints(points, OpenMaya.MSpace.kWorld)
        return points

    @staticmethod
    def get_nearest(point, search_points):
        """
        :param point: OpenMaya.MPoint
        :param search_points: OpenMaya.MPointArray
        :return: OpenMaya.MPoint
        """
        if not search_points:
            return
        nearest = search_points[0]
        distance = nearest.distanceTo(point)
        if search_points.length() > 2:
            for idx in xrange(1, search_points.length()):
                p = search_points[idx]
                new_distance = p.distanceTo(point)
                if new_distance < distance:
                    nearest = p
                    distance = new_distance
        return nearest


def initializePlugin(plugin):
    """
    Initialize the script plug-in
    :param plugin: OpenMayaMPx.MPxCommand
    """
    pluginFn = OpenMayaMPx.MFnPlugin(plugin)
    try:
        pluginFn.registerCommand(
            FitVertexCmd.kPluginCmdName, FitVertexCmd.cmd_creator
        )
    except:
        sys.stderr.write(
            "Failed to register command: %s\n" % FitVertexCmd.kPluginCmdName
        )
        raise


def uninitializePlugin(plugin):
    """
    Uninitialize the script plug-in
    :param plugin: OpenMayaMPx.MPxCommand
    """
    pluginFn = OpenMayaMPx.MFnPlugin(plugin)
    try:
        pluginFn.deregisterCommand(FitVertexCmd.kPluginCmdName)
    except:
        sys.stderr.write(
            "Failed to unregister command: %s\n" % FitVertexCmd.kPluginCmdName
        )
        raise
