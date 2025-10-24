# Leander Tenbarge


#Import CreateLoft
import WingLogic
import InputOutput
import CreateLoft
import gmsh
FilePath = "/Users/leandertenbarge/Desktop/3dCAD/Multi-Element-Wing-Generator/CaseFolder"
FileName = 'MultiElementWing'
NumSections = 50 
Scale = 1.5


gmsh.initialize()
gmsh.model.add("WingModel")

# Parsing the Input Files and defining the points:
WingSections = WingLogic.run(FilePath,NumSections)
InterpolatedArray = InputOutput.parse(FilePath)
EndplateData = InputOutput.parseEndPlate(FilePath)

# Creating the geometry Utilizing the GMSH API
Endplates = CreateLoft.buildEndplate(InterpolatedArray,EndplateData)
WireFrame = CreateLoft.createWireFrame(WingSections)
Wings = CreateLoft.buildLoft(WireFrame)
ScaledGeometry = CreateLoft.fuseScale(Scale=Scale,Wings=Wings,Endplates=Endplates)
Domain = CreateLoft.buildDomain(Height=5,Width=5,Ground=.5,Forward=5,Backward=10,Scale=Scale)
CreateLoft.domainBoolean(Wing=ScaledGeometry,Box=Domain)


# Exporting
gmsh.write("my_model.iges")


gmsh.fltk.run()
gmsh.finalize()














