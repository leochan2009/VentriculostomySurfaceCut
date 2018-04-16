import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy, sitkUtils, math
import SimpleITK as sitk
#
# VentriculostomySurfaceCut
#

class VentriculostomySurfaceCut(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "VentriculostomySurfaceCut" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["Longquan Chen (SPL.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# VentriculostomySurfaceCutWidget
#

class VentriculostomySurfaceCutWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

    #
    # output model selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLModelNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene(slicer.mrmlScene)
    self.outputSelector.setToolTip("Pick the output model to the algorithm.")
    parametersFormLayout.addRow("Output Model: ", self.outputSelector)

    #
    # input fiducial selector
    #
    self.inputNasionSelector = slicer.qMRMLNodeComboBox()
    self.inputNasionSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
    self.inputNasionSelector.selectNodeUponCreation = True
    self.inputNasionSelector.addEnabled = False
    self.inputNasionSelector.removeEnabled = False
    self.inputNasionSelector.noneEnabled = False
    self.inputNasionSelector.showHidden = False
    self.inputNasionSelector.showChildNodeTypes = False
    self.inputNasionSelector.setMRMLScene(slicer.mrmlScene)
    self.inputNasionSelector.setToolTip("Pick the input nasion node to the algorithm.")
    parametersFormLayout.addRow("Input Nasion node: ", self.inputNasionSelector)


    self.outCutModelSelector = slicer.qMRMLNodeComboBox()
    self.outCutModelSelector.nodeTypes = ["vtkMRMLModelNode"]
    self.outCutModelSelector.selectNodeUponCreation = True
    self.outCutModelSelector.addEnabled = True
    self.outCutModelSelector.removeEnabled = True
    self.outCutModelSelector.noneEnabled = True
    self.outCutModelSelector.showHidden = False
    self.outCutModelSelector.showChildNodeTypes = False
    self.outCutModelSelector.setMRMLScene(slicer.mrmlScene)
    self.outCutModelSelector.setToolTip("Pick the output model to the algorithm.")
    parametersFormLayout.addRow("Output cutted Model: ", self.outCutModelSelector)
    #
    # threshold value
    #
    self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget.singleStep = 0.1
    self.imageThresholdSliderWidget.minimum = -1000
    self.imageThresholdSliderWidget.maximum = 1000
    self.imageThresholdSliderWidget.value = 20
    self.imageThresholdSliderWidget.setToolTip("Set threshold value for computing the output image. Voxels that have intensities lower than this value will set to zero.")
    parametersFormLayout.addRow("Image threshold", self.imageThresholdSliderWidget)

    #
    # Apply Button
    #
    self.onCreateSurfaceButton = qt.QPushButton("CreateSurface")
    self.onCreateSurfaceButton.toolTip = "Create the surface."
    self.onCreateSurfaceButton.enabled = False
    parametersFormLayout.addRow(self.onCreateSurfaceButton)

    self.onCutSurfaceButton = qt.QPushButton("CutSurface")
    self.onCutSurfaceButton.toolTip = "Cut the surface base on the nasion point."
    self.onCutSurfaceButton.enabled = False
    parametersFormLayout.addRow(self.onCutSurfaceButton)

    # connections
    self.onCreateSurfaceButton.connect('clicked(bool)', self.onCreateSurface)
    self.onCutSurfaceButton.connect('clicked(bool)', self.onCutSurface)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.inputNasionSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outCutModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    self.logic = VentriculostomySurfaceCutLogic()
    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def onReload(self, moduleName="VentriculostomySurfaceCut"):
    self.cleanup()
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)
    self.logic = VentriculostomySurfaceCutLogic()

  def cleanup(self):
    self.logic.coronalReferenceCurveManager.clear()
    self.logic.sagittalReferenceCurveManager.clear()
    pass

  def onSelect(self):
    self.onCreateSurfaceButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()
    self.onCutSurfaceButton.enabled = self.inputSelector.currentNode() and self.inputNasionSelector.currentNode() and self.outputSelector.currentNode() and self.outCutModelSelector.currentNode()

  def onCreateSurface(self):
    imageThreshold = self.imageThresholdSliderWidget.value
    self.logic.createModel(self.inputSelector.currentNode(), self.outputSelector.currentNode(), imageThreshold)

  def onCutSurface(self):
    self.logic.cutSurface(self.outputSelector.currentNode(), self.inputNasionSelector.currentNode(), 100.0, 30.0, self.outCutModelSelector.currentNode())

#
# VentriculostomySurfaceCutLogic
#

class CurveManagerSurfaceCut():
  def __init__(self):
    try:
      import CurveMaker
    except ImportError:
      return slicer.util.warningDisplay(
        "Error: Could not find extension CurveMaker. Open Slicer Extension Manager and install "
        "CurveMaker.", "Missing Extension")
    self.cmLogic = CurveMaker.CurveMakerLogic()
    self.curveFiducials = None
    self._curveModel = None
    self.opacity = 1
    self.tubeRadius = 1.0
    self.curveName = ""
    self.curveModelName = ""
    self.step = 1
    self.tagEventExternal = None
    self.externalHandler = None

    self.sliceID = "vtkMRMLSliceNodeRed"
    modelNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLModelNode")
    slicer.mrmlScene.AddNode(modelNode)
    self.connectModelNode(modelNode)

    # Slice is aligned to the first point (0) or last point (1)
    self.slicePosition = 0

  def clear(self):
    if self._curveModel:
      slicer.mrmlScene.RemoveNode(self._curveModel.GetDisplayNode())
      slicer.mrmlScene.RemoveNode(self._curveModel)
    if self.curveFiducials:
      slicer.mrmlScene.RemoveNode(self.curveFiducials.GetDisplayNode())
      slicer.mrmlScene.RemoveNode(self.curveFiducials)
    self.curveFiducials = None
    self._curveModel = None

  def connectModelNode(self, mrmlModelNode):
    if self._curveModel:
      slicer.mrmlScene.RemoveNode(self._curveModel.GetDisplayNode())
      slicer.mrmlScene.RemoveNode(self._curveModel)
    self._curveModel = mrmlModelNode

  def connectMarkerNode(self, mrmlMarkerNode):
    if self.curveFiducials:
      slicer.mrmlScene.RemoveNode(self.curveFiducials.GetDisplayNode())
      slicer.mrmlScene.RemoveNode(self.curveFiducials)
    self.curveFiducials = mrmlMarkerNode

  def setName(self, name):
    self.curveName = name
    self.curveModelName = "%s-Model" % (name)
    self._curveModel.SetName(name)

  def setSliceID(self, name):
    # ID is either "vtkMRMLSliceNodeRed", "vtkMRMLSliceNodeYellow", or "vtkMRMLSliceNodeGreen"
    self.sliceID = name

  def setDefaultSlicePositionToFirstPoint(self):
    self.slicePosition = 0

  def setDefaultSlicePositionToLastPoint(self):
    self.slicePosition = 1

  def setModelColor(self, r, g, b):

    self.cmLogic.ModelColor = [r, g, b]

    # Make slice intersetion visible
    if self._curveModel:
      dnode = self._curveModel.GetDisplayNode()
      if dnode:
        dnode.SetColor([r, g, b])

    if self.curveFiducials:
      dnode = self.curveFiducials.GetMarkupsDisplayNode()
      if dnode:
        dnode.SetSelectedColor([r, g, b])

  def setModelOpacity(self, opacity):
    # Make slice intersetion visible
    self.opacity = opacity
    if self._curveModel:
      dnode = self._curveModel.GetDisplayNode()
      if dnode:
        dnode.opacity(opacity)

  def setManagerTubeRadius(self, radius):
    self.tubeRadius = radius

  def setModifiedEventHandler(self, handler=None):

    self.externalHandler = handler

    if self._curveModel:
      self.tagEventExternal = self._curveModel.AddObserver(vtk.vtkCommand.ModifiedEvent, self.externalHandler)
      return self.tagEventExternal
    else:
      return None

  def resetModifiedEventHandle(self):

    if self._curveModel and self.tagEventExternal:
      self._curveModel.RemoveObserver(self.tagEventExternal)

    self.externalHandler = None
    self.tagEventExternal = None

  def onLineSourceUpdated(self, caller=None, event=None):

    self.cmLogic.updateCurve()

    # Make slice intersetion visible
    if self._curveModel:
      dnode = self._curveModel.GetDisplayNode()
      if dnode:
        dnode.SetSliceIntersectionVisibility(1)

  def startEditLine(self, initPoint=None):

    if self.curveFiducials == None:
      self.curveFiducials = slicer.mrmlScene.CreateNodeByClass("vtkMRMLMarkupsFiducialNode")
      self.curveFiducials.SetName(self.curveName)
      slicer.mrmlScene.AddNode(self.curveFiducials)
      dnode = self.curveFiducials.GetMarkupsDisplayNode()
      if dnode:
        dnode.SetSelectedColor(self.cmLogic.ModelColor)
    if initPoint != None:
      self.curveFiducials.AddFiducial(initPoint[0], initPoint[1], initPoint[2])
      self.moveSliceToLine()

    if self._curveModel == None:
      self._curveModel = slicer.mrmlScene.CreateNodeByClass("vtkMRMLModelNode")
      self._curveModel.SetName(self.curveModelName)
      self.setModelOpacity(self.opacity)
      slicer.mrmlScene.AddNode(self._curveModel)
      modelDisplayNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLModelDisplayNode")
      modelDisplayNode.SetColor(self.cmLogic.ModelColor)
      modelDisplayNode.SetOpacity(self.opacity)
      slicer.mrmlScene.AddNode(modelDisplayNode)
      self._curveModel.SetAndObserveDisplayNodeID(modelDisplayNode.GetID())

    # Set exetrnal handler, if it has not been.
    if self.tagEventExternal == None and self.externalHandler:
      self.tagEventExternal = self._curveModel.AddObserver(vtk.vtkCommand.ModifiedEvent, self.externalHandler)

    self.cmLogic.DestinationNode = self._curveModel
    self.cmLogic.SourceNode = self.curveFiducials
    self.cmLogic.SourceNode.SetAttribute('CurveMaker.CurveModel', self.cmLogic.DestinationNode.GetID())
    self.cmLogic.updateCurve()

    self.cmLogic.CurvePoly = vtk.vtkPolyData()  ## For CurveMaker bug
    self.cmLogic.enableAutomaticUpdate(1)
    self.cmLogic.setInterpolationMethod(1)
    self.cmLogic.setTubeRadius(self.tubeRadius)

    self.tagSourceNode = self.cmLogic.SourceNode.AddObserver('ModifiedEvent', self.onLineSourceUpdated)

  def endEditLine(self):

    interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
    interactionNode.SetCurrentInteractionMode(slicer.vtkMRMLInteractionNode.ViewTransform)  ## Turn off

  def clearLine(self):

    if self.curveFiducials:
      self.curveFiducials.RemoveAllMarkups()
      # To trigger the initializaton, when the user clear the trajectory and restart the planning,
      # the last point of the coronal reference line should be added to the trajectory

    self.cmLogic.updateCurve()

    if self._curveModel:
      pdata = self._curveModel.GetPolyData()
      if pdata:
        pdata.Initialize()

  def getLength(self):

    return self.cmLogic.CurveLength

  def getFirstPoint(self, position):

    if self.curveFiducials == None:
      return False
    elif self.curveFiducials.GetNumberOfFiducials() == 0:
      return False
    else:
      self.curveFiducials.GetNthFiducialPosition(0, position)
      return True

  def getLastPoint(self, position):
    if self.curveFiducials == None:
      return False
    else:
      nFiducials = self.curveFiducials.GetNumberOfFiducials()
      if nFiducials == 0:
        return False
      else:
        self.curveFiducials.GetNthFiducialPosition(nFiducials - 1, position)
        return True

  def moveSliceToLine(self):

    viewer = slicer.mrmlScene.GetNodeByID(self.sliceID)

    if viewer == None:
      return

    if self.curveFiducials.GetNumberOfFiducials() == 0:
      return

    if self.slicePosition == 0:
      index = 0
    else:
      index = self.curveFiducials.GetNumberOfFiducials() - 1

    pos = [0.0] * 3
    self.curveFiducials.GetNthFiducialPosition(index, pos)

    if self.sliceID == "vtkMRMLSliceNodeRed":
      viewer.SetOrientationToAxial()
      viewer.SetSliceOffset(pos[2])
    elif self.sliceID == "vtkMRMLSliceNodeYellow":
      viewer.SetOrientationToSagittal()
      viewer.SetSliceOffset(pos[0])
    elif self.sliceID == "vtkMRMLSliceNodeGreen":
      viewer.SetOrientationToCoronal()
      viewer.SetSliceOffset(pos[1])

  def lockLine(self):

    if (self.curveFiducials):
      self.curveFiducials.SetDisplayVisibility(0)

  def unlockLine(self):

    if (self.curveFiducials):
      self.curveFiducials.SetDisplayVisibility(1)

class VentriculostomySurfaceCutLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    self.sagittalReferenceCurveManager = CurveManagerSurfaceCut()
    self.sagittalReferenceCurveManager.setName("SR1")
    self.sagittalReferenceCurveManager.setSliceID("vtkMRMLSliceNodeYellow")
    self.sagittalReferenceCurveManager.setDefaultSlicePositionToFirstPoint()
    self.sagittalReferenceCurveManager.setModelColor(1.0, 1.0, 0.5)

    self.coronalReferenceCurveManager = CurveManagerSurfaceCut()
    self.coronalReferenceCurveManager.setName("CR1")
    self.coronalReferenceCurveManager.setSliceID("vtkMRMLSliceNodeGreen")
    self.coronalReferenceCurveManager.setDefaultSlicePositionToLastPoint()
    self.coronalReferenceCurveManager.setModelColor(0.5, 1.0, 0.5)

    self.topPoint = []
    self.trueSagittalPlane = None
    self.useLeftHemisphere = False
    self.sagittalYawAngle = 0.0

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def createModel(self, ventricleVolume, outputModelNode, thresholdValue):
    resampleFilter = sitk.ResampleImageFilter()
    ventricleImage = sitk.Cast(sitkUtils.PullFromSlicer(ventricleVolume.GetID()), sitk.sitkInt16)
    samplingFactor = 2
    resampleFilter.SetSize(numpy.array(ventricleImage.GetSize()) / samplingFactor)
    resampleFilter.SetOutputSpacing(numpy.array(ventricleImage.GetSpacing()) * samplingFactor)
    resampleFilter.SetOutputDirection(ventricleImage.GetDirection())
    resampleFilter.SetOutputOrigin(numpy.array(ventricleImage.GetOrigin()))
    resampledImage = resampleFilter.Execute(ventricleImage)
    thresholdFilter = sitk.BinaryThresholdImageFilter()
    thresholdImage = thresholdFilter.Execute(resampledImage, thresholdValue, 10000, 1, 0)
    padFilter = sitk.ConstantPadImageFilter()
    padFilter.SetPadLowerBound([10, 10, 10])
    padFilter.SetPadUpperBound([10, 10, 10])
    paddedImage = padFilter.Execute(thresholdImage)
    dilateFilter = sitk.BinaryDilateImageFilter()
    dilateFilter.SetKernelRadius([7, 7, 5])
    dilateFilter.SetBackgroundValue(0)
    dilateFilter.SetForegroundValue(1)
    dilatedImage = dilateFilter.Execute(paddedImage)
    #dilatedImage_ori = vtk.vtkImageData(dilatedImage)
    erodeFilter = sitk.BinaryErodeImageFilter()
    erodeFilter.SetKernelRadius([5, 5, 3])
    erodeFilter.SetBackgroundValue(0)
    erodeFilter.SetForegroundValue(1)
    erodedImage = erodeFilter.Execute(dilatedImage)
    #subtractionFilter = sitk.SubtractImageFilter()
    #subtractedImage = subtractionFilter.Execute(dilatedImage_ori, erodedImage)
    fillHoleFilter = sitk.BinaryFillholeImageFilter()
    holefilledImage = fillHoleFilter.Execute(erodedImage)
    holefilledImageNode = sitkUtils.PushToSlicer(holefilledImage, "holefilledImage", 0, False)
    if holefilledImageNode:
      holefilledImageData = holefilledImageNode.GetImageData()
      cast = vtk.vtkImageCast()
      cast.SetInputData(holefilledImageData)
      cast.SetOutputScalarTypeToUnsignedChar()
      cast.Update()
      labelVolumeNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLLabelMapVolumeNode")
      slicer.mrmlScene.AddNode(labelVolumeNode)
      labelVolumeNode.SetName("Threshold")
      labelVolumeNode.SetSpacing(holefilledImageData.GetSpacing())
      labelVolumeNode.SetOrigin(holefilledImageData.GetOrigin())
      matrix = vtk.vtkMatrix4x4()
      holefilledImageNode.GetIJKToRASMatrix(matrix)
      labelVolumeNode.SetIJKToRASMatrix(matrix)
      labelImage = cast.GetOutput()
      labelVolumeNode.SetAndObserveImageData(labelImage)
      transformIJKtoRAS = vtk.vtkTransform()
      matrix = vtk.vtkMatrix4x4()
      labelVolumeNode.GetRASToIJKMatrix(matrix)
      transformIJKtoRAS.SetMatrix(matrix)
      transformIJKtoRAS.Inverse()
      padder = vtk.vtkImageConstantPad()
      padder.SetInputData(labelImage)
      padder.SetConstant(0)
      extent = labelImage.GetExtent()
      padder.SetOutputWholeExtent(extent[0], extent[1] + 2,
                                  extent[2], extent[3] + 2,
                                  extent[4], extent[5] + 2)
      cubes = vtk.vtkDiscreteMarchingCubes()
      cubes.SetInputConnection(padder.GetOutputPort())
      cubes.GenerateValues(1, 1, 1)
      cubes.Update()
      smoother = vtk.vtkWindowedSincPolyDataFilter()
      smoother.SetInputConnection(cubes.GetOutputPort())
      smoother.SetNumberOfIterations(10)
      smoother.BoundarySmoothingOn()
      smoother.FeatureEdgeSmoothingOff()
      smoother.SetFeatureAngle(120.0)
      smoother.SetPassBand(0.001)
      smoother.NonManifoldSmoothingOn()
      smoother.NormalizeCoordinatesOn()
      smoother.Update()
      pthreshold = vtk.vtkThreshold()
      pthreshold.SetInputConnection(smoother.GetOutputPort())
      pthreshold.ThresholdBetween(1, 1)  ## Label 1
      pthreshold.ReleaseDataFlagOn()
      geometryFilter = vtk.vtkGeometryFilter()
      geometryFilter.SetInputConnection(pthreshold.GetOutputPort())
      geometryFilter.ReleaseDataFlagOn()
      decimator = vtk.vtkDecimatePro()
      decimator.SetInputConnection(geometryFilter.GetOutputPort())
      decimator.SetFeatureAngle(60)
      decimator.SplittingOff()
      decimator.PreserveTopologyOn()
      decimator.SetMaximumError(1)
      decimator.SetTargetReduction(0.001)  # 0.001 only reduce the points by 0.1%, 0.5 is 50% off
      decimator.ReleaseDataFlagOff()
      decimator.Update()
      smootherPoly = vtk.vtkSmoothPolyDataFilter()
      smootherPoly.SetRelaxationFactor(0.33)
      smootherPoly.SetFeatureAngle(60)
      smootherPoly.SetConvergence(0)
      if transformIJKtoRAS.GetMatrix().Determinant() < 0:
        reverser = vtk.vtkReverseSense()
        reverser.SetInputConnection(decimator.GetOutputPort())
        reverser.ReverseNormalsOn()
        reverser.ReleaseDataFlagOn()
        smootherPoly.SetInputConnection(reverser.GetOutputPort())
      else:
        smootherPoly.SetInputConnection(decimator.GetOutputPort())
      Smooth = 10
      smootherPoly.SetNumberOfIterations(Smooth)
      smootherPoly.FeatureEdgeSmoothingOff()
      smootherPoly.BoundarySmoothingOff()
      smootherPoly.ReleaseDataFlagOn()
      smootherPoly.Update()
      transformer = vtk.vtkTransformPolyDataFilter()
      transformer.SetInputConnection(smootherPoly.GetOutputPort())
      transformer.SetTransform(transformIJKtoRAS)
      transformer.ReleaseDataFlagOn()
      transformer.Update()
      normals = vtk.vtkPolyDataNormals()
      normals.SetInputConnection(transformer.GetOutputPort())
      normals.SetFeatureAngle(60)
      normals.SetSplitting(True)
      normals.ReleaseDataFlagOn()
      stripper = vtk.vtkStripper()
      stripper.SetInputConnection(normals.GetOutputPort())
      stripper.ReleaseDataFlagOff()
      stripper.Update()
      outputModel = stripper.GetOutput()
      outputModelNode.SetAndObservePolyData(outputModel)
      outputModelNode.CreateDefaultDisplayNodes()
      outputModelNode.SetAttribute("vtkMRMLModelNode.modelCreated", "True")
      outputModelNode.GetDisplayNode().SetVisibility(1)
      outputModelNode.GetDisplayNode().SetOpacity(0.2)
      return

  def createTrueSagittalPlane(self, nasionNode):
      if nasionNode.GetNumberOfFiducials():
        posNasion = numpy.array([0.0, 0.0, 0.0])
        posSagittal = numpy.array([0.0, 0.0, 0.0])
        nasionNode.GetNthFiducialPosition(0, posNasion)
        if nasionNode.GetNumberOfFiducials() > 1:
          nasionNode.GetNthFiducialPosition(1, posSagittal)
          self.sagittalYawAngle = -numpy.arctan2(posNasion[0] - posSagittal[0], posNasion[1] - posSagittal[1])
        else:
          self.sagittalYawAngle = 0
        self.trueSagittalPlane = vtk.vtkPlane()
        self.trueSagittalPlane.SetOrigin(posNasion[0], posNasion[1], posNasion[2])
        self.trueSagittalPlane.SetNormal(math.cos(self.sagittalYawAngle), math.sin(self.sagittalYawAngle), 0)

  def cutSurface(self, inputModelNode, nasionNode, sagittalReferenceLength, coronalReferenceLength, outputModelNode):
    ###All calculation is based on the RAS coordinates system
    if inputModelNode and (nasionNode.GetNumberOfMarkups()):
      cube = vtk.vtkCubeSource()
      box = vtk.vtkBox()
      clipper = vtk.vtkClipPolyData()
      posNasion = numpy.array([0.0, 0.0, 0.0])
      nasionNode.GetNthFiducialPosition(nasionNode.GetNumberOfMarkups() - 1, posNasion)
      cube.SetCenter(posNasion[0], posNasion[1], posNasion[2])
      cube.SetXLength(100)
      cube.SetYLength(50)
      cube.SetZLength(50)
      cube.Update()
      box.SetBounds(cube.GetOutput().GetBounds())
      clipper.SetClipFunction(box)
      clipper.SetInputData(inputModelNode.GetPolyData())
      clipper.InsideOutOn()
      clipper.Update()
      outputPoly = clipper.GetOutput()
      outputModelNode.CreateDefaultDisplayNodes()
      outputModelNode.SetAttribute("vtkMRMLModelNode.modelCreated", "True")
      outputModelNode.GetDisplayNode().SetVisibility(1)
      outputModelNode.GetDisplayNode().SetOpacity(0.6)
      self.generateKocherNav(inputModelNode, nasionNode, sagittalReferenceLength, coronalReferenceLength)
      appendFilter = vtk.vtkAppendPolyData()
      appendFilter.AddInputData(clipper.GetOutput())
      appendFilter.AddInputData(self.sagittalReferenceCurveManager._curveModel.GetPolyData())
      appendFilter.Update()
      outputPoly.DeepCopy(appendFilter.GetOutput())
      appendFilter.RemoveAllInputs()
      appendFilter.AddInputData(outputPoly)
      appendFilter.AddInputData(self.coronalReferenceCurveManager._curveModel.GetPolyData())
      appendFilter.Update()
      outputModelNode.SetAndObservePolyData(appendFilter.GetOutput())
      appendFilter.RemoveAllInputs()
    pass

  def generateKocherNav(self, inputModelNode, nasionNode, sagittalReferenceLength, coronalReferenceLength):
    polyData = inputModelNode.GetPolyData()
    self.createTrueSagittalPlane(nasionNode)
    if polyData and self.trueSagittalPlane and nasionNode.GetNumberOfMarkups() > 0:
      posNasion = numpy.array([0.0, 0.0, 0.0])
      nasionNode.GetNthFiducialPosition(nasionNode.GetNumberOfMarkups() - 1, posNasion)
      sagittalPoints = vtk.vtkPoints()
      self.getIntersectPoints(polyData, self.trueSagittalPlane, posNasion, sagittalReferenceLength, 0, sagittalPoints)
      ## Sorting
      self.sortPoints(sagittalPoints, posNasion)
      self.constructCurveReference(self.sagittalReferenceCurveManager, sagittalPoints, sagittalReferenceLength)
      ##To do, calculate the curvature value points by point might be necessary to exclude the outliers
      if self.topPoint:
        posNasionBack100 = self.topPoint
        coronalPoints = vtk.vtkPoints()
        coronalPlane = vtk.vtkPlane()
        coronalPlane.SetOrigin(posNasionBack100[0], posNasionBack100[1], posNasionBack100[2])
        coronalPlane.SetNormal(math.sin(self.sagittalYawAngle), -math.cos(self.sagittalYawAngle), 0)
        coronalPoints.InsertNextPoint(posNasionBack100)
        self.getIntersectPoints(polyData, coronalPlane, posNasionBack100, coronalReferenceLength, 1, coronalPoints)

        ## Sorting
        self.sortPoints(coronalPoints, posNasionBack100)
        self.constructCurveReference(self.coronalReferenceCurveManager, coronalPoints, coronalReferenceLength)
        posEntry = [0.0, 0.0, 0.0]
        self.coronalReferenceCurveManager.getLastPoint(posEntry)

  def getIntersectPoints(self, polyData, plane, referencePoint, targetDistance, axis, intersectPoints):
    cutter = vtk.vtkCutter()
    cutter.SetCutFunction(plane)
    cutter.SetInputData(polyData)
    cutter.Update()
    cuttedPolyData = cutter.GetOutput()
    points = cuttedPolyData.GetPoints()
    for iPos in range(points.GetNumberOfPoints()):
      posModel = numpy.array(points.GetPoint(iPos))
      ## distance calculation could be simplified if the patient is well aligned in the scanner
      distanceModelNasion = numpy.linalg.norm(posModel - referencePoint)
      valid = False
      if axis == 0:
        valid = posModel[2] >= referencePoint[2]
      elif axis == 1:
        if self.useLeftHemisphere:
          valid = posModel[0] <= referencePoint[0]
        else:
          valid = posModel[0] >= referencePoint[0]
      if (distanceModelNasion < targetDistance) and valid:
        intersectPoints.InsertNextPoint(posModel)

  def sortPoints(self, inputPointVector, referencePoint):
    minDistanceIndex = 0
    minDistance = 1e10
    for iPos in range(inputPointVector.GetNumberOfPoints()):
      currentPos = numpy.array(inputPointVector.GetPoint(iPos))
      minDistance = numpy.linalg.norm(currentPos - referencePoint)
      minDistanceIndex = iPos
      for jPos in range(iPos, inputPointVector.GetNumberOfPoints()):
        posModelPost = numpy.array(inputPointVector.GetPoint(jPos))
        distanceModelPostNasion = numpy.linalg.norm(posModelPost - referencePoint)
        if distanceModelPostNasion < minDistance:
          minDistanceIndex = jPos
          minDistance = distanceModelPostNasion
      inputPointVector.SetPoint(iPos, inputPointVector.GetPoint(minDistanceIndex))
      inputPointVector.SetPoint(minDistanceIndex, currentPos)

  def constructCurveReference(self, CurveManager, points, distance):
    step = int(0.1 * points.GetNumberOfPoints())
    CurveManager.step = step
    ApproximityPos = distance * 0.85
    DestiationPos = distance

    if CurveManager.curveFiducials == None:
      CurveManager.curveFiducials = slicer.mrmlScene.CreateNodeByClass("vtkMRMLMarkupsFiducialNode")
      CurveManager.curveFiducials.SetName(CurveManager.curveName)
      slicer.mrmlScene.AddNode(CurveManager.curveFiducials)
    else:
      CurveManager.curveFiducials.RemoveAllMarkups()
      CurveManager.cmLogic.updateCurve()

    iPos = 0
    iPosValid = iPos
    posModel = numpy.array(points.GetPoint(iPos))
    CurveManager.cmLogic.DestinationNode = CurveManager._curveModel
    CurveManager.curveFiducials.AddFiducial(posModel[0], posModel[1], posModel[2])
    CurveManager.cmLogic.CurvePoly = vtk.vtkPolyData()  ## For CurveMaker bug
    # CurveManager.cmLogic.enableAutomaticUpdate(1)
    # CurveManager.cmLogic.setInterpolationMethod(1)
    # CurveManager.cmLogic.setTubeRadius(1.0)
    for iPos in range(step, points.GetNumberOfPoints(), step):
      posModel = numpy.array(points.GetPoint(iPos))
      posModelValid = numpy.array(points.GetPoint(iPosValid))
      if numpy.linalg.norm(posModel - posModelValid) > 50.0:
        continue
      iPosValid = iPos
      CurveManager.curveFiducials.AddFiducial(posModel[0], posModel[1], posModel[
        2])  # adding fiducials takes too long, check the event triggered by this operation
      CurveManager.cmLogic.SourceNode = CurveManager.curveFiducials
      CurveManager.cmLogic.updateCurve()
      if CurveManager.cmLogic.CurveLength > ApproximityPos:
        break
    jPos = iPosValid
    jPosValid = jPos
    posApprox = numpy.array(points.GetPoint(iPos))
    for jPos in range(iPosValid, points.GetNumberOfPoints(), 1):
      posModel = numpy.array(points.GetPoint(jPos))
      posModelValid = numpy.array(points.GetPoint(jPosValid))
      if numpy.linalg.norm(posModel - posModelValid) > 50.0:
        continue
      distance = numpy.linalg.norm(posModel - posApprox) + CurveManager.cmLogic.CurveLength
      if (distance > DestiationPos) or (jPos == points.GetNumberOfPoints() - 1):
        CurveManager.curveFiducials.AddFiducial(posModel[0], posModel[1], posModel[2])
        jPosValid = jPos
        break
    CurveManager.cmLogic.updateCurve()
    CurveManager.cmLogic.CurvePoly = vtk.vtkPolyData()  ## For CurveMaker bug
    CurveManager.cmLogic.enableAutomaticUpdate(1)
    CurveManager.cmLogic.setInterpolationMethod(1)
    CurveManager.cmLogic.setTubeRadius(0.5)
    self.topPoint = points.GetPoint(jPos)


class VentriculostomySurfaceCutTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_VentriculostomySurfaceCut1()

  def test_VentriculostomySurfaceCut1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = VentriculostomySurfaceCutLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
