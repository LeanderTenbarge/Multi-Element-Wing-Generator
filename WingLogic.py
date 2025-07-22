import numpy as np
from scipy.special import comb
import InputOutput
import CreateLoft


# Wing Section Class
class wing_section:
    def __init__(self, kernel, z):
        self.element = []
        self.coordinates = []
        

        for i in range(kernel.shape[1]):
            chromosome = kernel[:, i]
            self.scale = chromosome[17] # Scale

            if i != 0:
                if self.element[i - 1] is not None:
                    chromosome[13], chromosome[14] = self.element[i - 1].return_max()
                    chromosome[13] -= chromosome[15] #Overlap
                    chromosome[14] += chromosome[16] #Slotgap
                    
                else:
                    # Skip or handle chaining when previous element is missing
                    self.element.append(None)
                    self.coordinates.append(None)
                    continue

            if self.scale != 0:
                strand = profile(chromosome)
                self.x = np.array(strand.x)
                self.y = np.array(strand.y)
                self.z = z * np.ones_like(strand.x)
                self.element.append(strand)
                self.coordinates.append(np.column_stack((self.x, self.y, self.z)))
            else:
                self.element.append(None)
                self.coordinates.append(None)

# Airfoil profile class
class profile:
    def __init__(self,input_parameters):
        self.parameters_upper = np.array(input_parameters[0:7])
        self.parameters_lower = np.array(input_parameters[7:13])
        #self.parameters_camber = np.array(input_parameters[12:14])
        self.parameters_angle = np.array((input_parameters[12]))
        self.parameters_offset = np.array(input_parameters[13:15])
        self.parameters_scale = np.array(input_parameters[17])
        self.x = []
        self.y = []
        self.change_thickness()
        self.rotate()
        self.scale()
    
    def change_thickness(self):
        beta = np.linspace(0, np.pi, 30)
        x_dist = 0.5 * (1 - np.cos(beta))   
        y_upper = [((x**.5)*(1 - x)**1) * sum(self.parameters_upper[i] * comb(len(self.parameters_upper) - 1, i) * x**i * (1 - x)**(len(self.parameters_upper) - 1 - i) for i in range(len(self.parameters_upper))) for x in x_dist]
        y_lower = [-((x**.5)*(1 - x)**1) * sum(self.parameters_lower[i] * comb(len(self.parameters_lower) - 1, i) * x**i * (1 - x)**(len(self.parameters_lower) - 1 - i) for i in range(len(self.parameters_lower))) for x in x_dist]
        x_upper = np.flip(x_dist)
        y_upper = np.flip(y_upper)
        x_lower = x_dist[1:]
        y_lower = y_lower[1:]
        self.x = np.concatenate((x_upper, x_lower))
        self.y = np.concatenate((y_upper, y_lower))
        return self.x, self.y
    
    
    def rotate(self):
        r_matrix = np.array([[np.cos(self.parameters_angle) , -np.sin(self.parameters_angle)],[np.sin(self.parameters_angle) , np.cos(self.parameters_angle)]])
        points = [
        (
            x * r_matrix[0][0] + y * r_matrix[0][1],  
            x * r_matrix[1][0] + y * r_matrix[1][1]  
        )
        for x, y in zip(self.x, self.y)
        ]
        self.x,self.y = zip(*points)
        self.x = np.array(self.x)
        self.y = np.array(self.y)

    def scale(self):
        self.x = self.x * self.parameters_scale + self.parameters_offset[0]
        self.y = self.y * self.parameters_scale + self.parameters_offset[1]

    def return_max(self):
        return self.x[0], self.y[0]
    
def run(FilePath,NumberSections):
    # Collecting Data and Initializing arrays
    dist = np.linspace(0, 1, NumberSections)
    kernel_list = []
    WingSections = []
    InterpolatedArray = InputOutput.parse(FilePath)

    # For each z in dist, compute kernels for all data sets
    for z in dist:
        PlaceHolder = np.zeros_like(InterpolatedArray)
        for i in range(np.shape(InterpolatedArray)[0]):
            for j in range(np.shape(InterpolatedArray)[1]):
                PlaceHolder[i,j] = InterpolatedArray[i,j](z)
        kernel_list.append(PlaceHolder)
        
    #Determine the Wing Sections from the kernels
    for j, kernel in enumerate(kernel_list):
        z = dist[j]
        ws = wing_section(kernel, z)
        WingSections.append(ws)

    return WingSections


    
    
