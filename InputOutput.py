import pandas as pd
import numpy as np
import os 
from scipy.interpolate import PchipInterpolator
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.StlAPI import StlAPI_Writer
from OCP.IGESControl import IGESControl_Writer
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepMesh import BRepMesh_IncrementalMesh



def process(path):
    Interpolators = []

    #Extracting the Data from the .CSV files
    UpperData = pd.read_csv(os.path.join(path,'UpperInput.csv'))
    LowerData = pd.read_csv(os.path.join(path,'LowerInput.csv'))
    ParameterData = pd.read_csv(os.path.join(path,'Parameters.csv'))

    #Combining the Dataframes into an array
    CombinedData = pd.concat([UpperData,LowerData,ParameterData], axis = 1)

    #Initalizing the X and Y lists for the extraction from the Combined Dataframe.
    zList = ['u1z','u2z','u3z','u4z','u5z','u6z','l1z','l2z','l3z','l4z','l5z','l6z','az','xoffz','yoffz','ovlpz','slz','sclz']
    yList = ['u1y','u2y','u3y','u4y','u5y','u6y','l1y','l2y','l3y','l4y','l5y','l6y','ay','xoffy','yoffy','ovlpy','sly','scly']


    #Calculating the Interpolators  
    for i in range(len(zList)):
        FilteredZdata = [i for i in CombinedData[zList[i]].values if not np.isnan(i)]
        FilteredYdata = [i for i in CombinedData[yList[i]].values if not np.isnan(i)]
        Interpolators.append(PchipInterpolator(FilteredZdata,FilteredYdata, extrapolate=False))

    return Interpolators
        
def processEndplate(Filename):
    EndPlateData = pd.read_csv(Filename) 
    columns = ['HOff1', 'VoffUpp1', 'VoffLow1','HOff2', 'VoffUpp2', 'VoffLow2','Thickness','z']

    # Extract and flatten row-wise, then reshape to column vector
    filtered_data = EndPlateData[columns].values.flatten().reshape(-1, 1)
    return filtered_data

def parse(FilePath):
        
    # Changing Directories to the Case File Path and determining how many elements (Folders) this case file has. 
    wings = os.path.join(FilePath,'Wings')
    os.chdir(wings)
    NumberElements = len(os.listdir())
    SubDirectories = []
    Interpolators = []

    # Creating the list of subdirectories
    for i in range(NumberElements):
            SubDirectories.append(os.path.join(wings,str(i+1)))
        
    # Processing the Data from the .CSV files
    for path in SubDirectories:
        Interpolators.append(process(path))
    
    os.chdir(FilePath)
    return np.vstack(Interpolators).T
        
def parseEndPlate(FilePath):
    plates = os.path.join(FilePath,'Endplates')
    os.chdir(plates)
    data = []

    # For Each File Run the Endplate Processing Script 
    for file in os.listdir():
        result = processEndplate(file)
        data.append(result)
         
    # Vertically stack the answers and return the array of information
    os.chdir(FilePath)
    return np.vstack(data)

def Export(FusedGeometry,filename,FilePath):
    ExportPath = os.path.join(FilePath,'GeometryFiles')
    os.chdir(ExportPath)

    # Export STEP
    step_writer = STEPControl_Writer()
    step_writer.Transfer(FusedGeometry, STEPControl_AsIs)
    step_writer.Write(f"{filename}.step")
    

    # Export IGES
    iges_writer = IGESControl_Writer()
    iges_writer.AddShape(FusedGeometry)
    iges_writer.Write(f"{filename}.iges")


    #Mesh before STL export
    mesh = BRepMesh_IncrementalMesh(FusedGeometry, 0.00001) # Mesh Density
    mesh.Perform()

    # Export STL
    stl_writer = StlAPI_Writer()
    stl_writer.ASCIIMode = False  
    stl_writer.Write(FusedGeometry , f"{filename}.stl")

    os.chdir(FilePath)




