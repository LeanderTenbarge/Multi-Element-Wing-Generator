
import gmsh
import numpy as np
import WingLogic

# Fuses and Scales the Entire Geometry around the origin (0,0,0):
def fuseScale(Scale,Wings,Endplates): 
    
    #Fusing the Components:
    Wings = Wings + Endplates
    Shape = Wings[0]
    for tag in Wings[1:]:
        Shape, _ = gmsh.model.occ.fuse(Shape, tag, removeObject=True, removeTool=True)
    
    # Dialating the Fused Components:
    gmsh.model.occ.dilate(Shape,0,0,0,Scale,Scale,Scale)
    gmsh.model.occ.synchronize()
    
    return Shape

# Creates the OCC wireFrame objects from edges and points
def createWireFrame(WingSections):

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
                # Creating the points:
                points = [gmsh.model.occ.addPoint(WingSections[i].coordinates[j][k][0],WingSections[i].coordinates[j][k][1],WingSections[i].coordinates[j][k][2],) for k in range(WingSections[i].coordinates[j].shape[0])]

                # Create Lines between consecutive points:
                lines = [gmsh.model.occ.addLine(points[k], points[k + 1]) for k in range(len(points) - 1)]

                # Create the Wire:
                wire = gmsh.model.occ.addWire(lines)
                wires[i, j] = (1, wire)

            except Exception:
                wires[i,j] = None

    return wires

def buildLoft(wires):
    LoftedSurfaces = []



    # Looping over the Elements
    for j in range(wires.shape[1]):  
        loft_sections = []
        valid_wires = 0

        #Looping over the spanwise profiles
        for i in range(wires.shape[0]):  
            wire = wires[i, j]

            # Determining if the section is valid
            if wire is not None:
                if isinstance(wire, tuple) and len(wire) == 2:
                    loft_sections.append(wire[1])  
                    valid_wires += 1
                else:
                    continue

            elif i != 0 and wires[i-1, j] is not None:
                if valid_wires >= 2:
                    loft = gmsh.model.occ.addThruSections(loft_sections, makeSolid=True)
                    LoftedSurfaces.append(loft)

                # Reset for next sequence
                loft_sections = []
                valid_wires = 0
                continue


        # Catch case where the final wire sequence reaches the end
        if valid_wires >= 2:
            loft = gmsh.model.occ.addThruSections(loft_sections, makeSolid=True)
            LoftedSurfaces.append(loft)

    gmsh.model.occ.synchronize()
    return LoftedSurfaces

def buildEndplate(InterpolatorArray, DataArray):
    Endplates = []

    # Determining the kernel for the theoretical wing section. 
    kernel = np.zeros_like(InterpolatorArray)

    for i in range(np.shape(DataArray)[1]):
        for j in range(np.shape(InterpolatorArray)[0]):
            for k in range(np.shape(InterpolatorArray)[1]):
                kernel[j, k] = InterpolatorArray[j, k](DataArray[7, i])

        section = WingLogic.wing_section(kernel, DataArray[7, i])

        MaximumValue = section.coordinates[-1][-1]
        Index = int(len(section.coordinates[-1]) / 2)
        MinimumValue = section.coordinates[0][Index]

        # Determining the points needed for the actual geometry.
        PointOne = MinimumValue + np.array([-DataArray[0, i], DataArray[1, i], 0.0])
        PointTwo = MinimumValue + np.array([-DataArray[0, i], -DataArray[2, i], 0.0])
        PointThree = MaximumValue + np.array([DataArray[3, i], DataArray[4, i], 0.0])
        PointFour = MaximumValue + np.array([DataArray[3, i], -DataArray[5, i], 0.0])

        # Add points in Gmsh
        p1 = gmsh.model.occ.addPoint(PointOne[0], PointOne[1], PointOne[2])
        p2 = gmsh.model.occ.addPoint(PointTwo[0], PointTwo[1], PointTwo[2])
        p3 = gmsh.model.occ.addPoint(PointThree[0], PointThree[1], PointThree[2])
        p4 = gmsh.model.occ.addPoint(PointFour[0], PointFour[1], PointFour[2])

        # Create edges
        e1 = gmsh.model.occ.addLine(p1, p2)
        e2 = gmsh.model.occ.addLine(p2, p4)
        e3 = gmsh.model.occ.addLine(p4, p3)
        e4 = gmsh.model.occ.addLine(p3, p1)

        # Create wire
        wire = gmsh.model.occ.addWire([e1, e2, e3, e4])

        # Create face
        face = gmsh.model.occ.addPlaneSurface([wire])

        # Extrude the face (prism), extrude returns surface tags too. 
        extrusion = gmsh.model.occ.extrude([(2, face)], 0, 0, DataArray[6, i])
        solidTag = [tag for tag in extrusion if tag[0] == 3]
        Endplates.append(solidTag)
    

    gmsh.model.occ.synchronize()
    return Endplates

def buildDomain(Height,Width,Ground,Forward,Backward,Scale):
        
        # Creating the groups for the name
        surfaces = gmsh.model.getEntities(2)
        tags = [tag for dim, tag in surfaces]
        group = gmsh.model.addPhysicalGroup(2, tags)
        gmsh.model.setPhysicalName(2, group, "Wing.NS")
        
        
        
        Domain = []

        # Add points in Gmsh with the Scaled Coordinates
        p1 = gmsh.model.occ.addPoint(-Forward*Scale,-Ground*Scale,0)
        p2 = gmsh.model.occ.addPoint(-Forward*Scale,(Height-Ground)*Scale, 0 )
        p3 = gmsh.model.occ.addPoint(Backward*Scale,(Height-Ground)*Scale, 0 )
        p4 = gmsh.model.occ.addPoint(Backward*Scale,-Ground*Scale,0)

        # Create edges:
        e1 = gmsh.model.occ.addLine(p1, p2)
        e2 = gmsh.model.occ.addLine(p2, p3)
        e3 = gmsh.model.occ.addLine(p3, p4)
        e4 = gmsh.model.occ.addLine(p4, p1)

        # Create wire:
        wire = gmsh.model.occ.addWire([e1, e2, e3, e4])

        # Create face
        face = gmsh.model.occ.addPlaneSurface([wire])

        # Extrude the face (prism), extrude returns surface tags too. 
        extrusion = gmsh.model.occ.extrude([(2, face)], 0, 0, Width)
        solidTag = [tag for tag in extrusion if tag[0] == 3]
        gmsh.model.occ.synchronize()
        Domain.append(solidTag)
        return Domain

def domainBoolean(Wing,Box):
    Box = [sub[0] for sub in Box]
    domainTags,_ = gmsh.model.occ.cut(objectDimTags=Box,toolDimTags=Wing, removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    return domainTags

def writeGroups(Height,Width,Ground,Forward,Backward,Scale):
    gmsh.model.occ.synchronize()
    print(gmsh.model.occ.get_entities_in_bounding_box((Backward*Scale)/4,-1,-1,(Backward*Scale)/3,Height*Scale+1,Width*Scale+1,dim=3))
    print(gmsh.model.occ.getEntitiesInBoundingBox((Backward*Scale)/4,-1,-1,(Backward*Scale)/3,Height*Scale+1,Width*Scale+1,dim=3))
