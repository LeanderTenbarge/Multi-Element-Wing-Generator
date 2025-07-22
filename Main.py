# Leander Tenbarge
import CreateLoft
import WingLogic
import InputOutput


FilePath = "/Users/leandertenbarge/Desktop/Multi-Element scripting/CaseFolder"
FileName = 'MultiElementWing'
NumSections = 50 
Scale = 1.5


WingSections = WingLogic.run(FilePath,NumSections)
InterpolatedArray = InputOutput.parse(FilePath)
EndplateData = InputOutput.parseEndPlate(FilePath)
Endplates = CreateLoft.BuildEndplate(InterpolatedArray,EndplateData)
WireFrame = CreateLoft.CreateWireFrame(WingSections)
Wings = CreateLoft.BuildLoft(WireFrame)
Geometry = CreateLoft.CreateGeometry(Wings,Endplates)
ScaledGeometry = CreateLoft.Scale(Scale,Geometry)
InputOutput.Export(ScaledGeometry,FileName,FilePath)








