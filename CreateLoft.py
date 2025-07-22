from OCP.gp import gp_Pnt,gp_Vec, gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepMesh import BRepMesh_IncrementalMesh
import numpy as np
import WingLogic

def Scale(Scale,Shape):
    trsf = gp_Trsf()
    trsf.SetScale(gp_Pnt(0,0,0),Scale)
    return BRepBuilderAPI_Transform(Shape,trsf,True).Shape()

# Creates the OCC wireFrame objects from edges and points
def CreateWireFrame(WingSections):

    # Determine the max number of foil profiles across all spanwise sections
    TotalFoils = max(len(section.coordinates) for section in WingSections)

    # Initialize wires as a 2D object array [spanwise_section, profile_index]
    wires = np.empty([len(WingSections), TotalFoils], dtype=object)

    # Loop over spanwise sections and profiles
    for i in range(len(WingSections)):
        for j in range(len(WingSections[i].coordinates)):
            if WingSections[i].coordinates[j] is None:
                wires[i, j] = None
                continue

            try:
                points = [gp_Pnt(*WingSections[i].coordinates[j][k]) for k in range(WingSections[i].coordinates[j].shape[0])]
                
                # Create edges between consecutive points
                edges = [BRepBuilderAPI_MakeEdge(points[k], points[k + 1]).Edge()
                         for k in range(len(points) - 1)]

                # Build wire from edges
                wire_maker = BRepBuilderAPI_MakeWire()
                for edge in edges:
                    wire_maker.Add(edge)
                wires[i, j] = wire_maker.Wire()

            except Exception:
                wires[i,j] = None
            
    return wires

# Takes the Wires and returns a list of Loft objects.
def BuildLoft(wires):
    LoftedSurfaces = []

    # Constructs the Lofts
    for j in range(wires.shape[1]):

        # Creating the initial Lofts for each Element
        loft = BRepOffsetAPI_ThruSections(True, False, 1e-6)
        valid_wires = 0  # Track how many wires have been added

        for i in range(wires.shape[0]):
            wire = wires[i, j]

            if wire is not None:
                loft.AddWire(wire)
                valid_wires += 1

            elif i != 0 and wires[i-1, j] is not None:
                if valid_wires >= 2:
                    loft.Build()
                    LoftedSurfaces.append(loft.Shape())
                loft = BRepOffsetAPI_ThruSections(True, False, 1e-6)
                valid_wires = 0
                continue

        # Catch case where the final wire sequence reaches the end without hitting None
        if valid_wires >= 2:
            loft.Build()
            LoftedSurfaces.append(loft.Shape())

    return LoftedSurfaces

# Constructing the EndPlates
def BuildEndplate(InterpolatorArray,DataArray):
    Endplates = []
 
    #Determining the kernel for the theoretical wing section. 
    kernel = np.zeros_like(InterpolatorArray)
    
    # Needs to be a for Loop for the different columns in Data Array
    for i in range(np.shape(DataArray)[1]):
        for j in range(np.shape(InterpolatorArray)[0]):
            for k in range(np.shape(InterpolatorArray)[1]):
                kernel[j,k] = InterpolatorArray[j,k](DataArray[7,i])

        section = WingLogic.wing_section(kernel,DataArray[7,i])

        MaximumValue = section.coordinates[-1][-1]
        Index = int(len(section.coordinates[-1])/2)
        MinimumValue = section.coordinates[0][Index]
     
        # Determining the points needed for the actual geometry.
        PointOne = MinimumValue + np.array([-DataArray[0, i],DataArray[1, i],0.0])
        PointTwo = MinimumValue + np.array([-DataArray[0, i],-DataArray[2, i],0.0])
        PointThree = MaximumValue + np.array([DataArray[3, i],DataArray[4, i],0.0])
        PointFour = MaximumValue + np.array([DataArray[3, i],-DataArray[5, i],0.0])

        # Creating the Points in the Api
        PointOne = gp_Pnt(PointOne[0],PointOne[1],PointOne[2])
        PointTwo = gp_Pnt(PointTwo[0],PointTwo[1],PointTwo[2])
        PointThree = gp_Pnt(PointThree[0],PointThree[1],PointThree[2])
        PointFour = gp_Pnt(PointFour[0],PointFour[1],PointFour[2])

        # Creating the Edges
        edgeOne = BRepBuilderAPI_MakeEdge(PointOne,PointTwo).Edge()
        edgeTwo = BRepBuilderAPI_MakeEdge(PointTwo,PointFour).Edge()
        edgeThree = BRepBuilderAPI_MakeEdge(PointFour,PointThree).Edge()
        edgeFour = BRepBuilderAPI_MakeEdge(PointThree,PointOne).Edge()
            
        #Creating the Wire
        wire = BRepBuilderAPI_MakeWire(edgeOne,edgeTwo,edgeThree,edgeFour).Wire()

        # Creating the Face
        face = BRepBuilderAPI_MakeFace(wire).Face()

        # Creating the the Extrude 
        solid = BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, DataArray[6,i])).Shape()
        BRepMesh_IncrementalMesh(solid, 0.0002, True, 0.1, True)
        Endplates.append(solid)

    return Endplates

def CreateGeometry(Wings, Endplates):
    # Fuse all wings
    fused_wing = Wings[0]
    for wing in Wings[1:]:
        fuse_op = BRepAlgoAPI_Fuse(fused_wing, wing)
        fuse_op.Build()
        if fuse_op.IsDone():
            fused_wing = fuse_op.Shape()
        else:
            pass

    # Fuse all endplates
    FusedGeometry = fused_wing
    for endplate in Endplates:
        fuse_op = BRepAlgoAPI_Fuse(FusedGeometry, endplate)
        fuse_op.Build()
        if fuse_op.IsDone():
            FusedGeometry = fuse_op.Shape()
        else:
            pass

    return FusedGeometry