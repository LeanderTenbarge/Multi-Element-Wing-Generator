# Multi-Element-Wing-Generator
## Overview
The main motivation for this project is to develop parametric modeling techniques of a multi-element wing structure using a novel combination of:
1. Class Shape Transformations (CST) 
2. Piecewise Cubic Hermite Interpolating Polynomials (PCHIP).

This provides us the following benefits/features.
1. Flexible and efficient fine tuning capabilities allowing for efficient design work flow.
2. Adaptible and versatile enough for coupling with optimization routines.
3. Support for Multiple wings and endplates, with the ability to have certain elements only in certain spanwise ranges
4. Ability to analyse and design around endplate - wing interactions.
5. Scalable Geometry Export in .STEP,.IGES ,and STL file configurations.

## Table of Contents:
1. Installation Methods
2. General Outline of the Problem
3. Shape Transformations 
4. PCHIP Interpolations
5. NACA 4 Digit Camber Function
6. Case Folder Structure and explanation
7. Example Usage and Photos
8. Future plans and Licensing

## Installation
 - In order to utilize the necessary modules and packages for this code to work we are using python 3.10 managed through a conda environment.
### Copying the Repository to the Current Directory
```bash 
git clone https://github.com/yourusername/Multi-Element-Wing-Generator.git
cd Multi-Element-Wing-Generator
```

### Utilizing the .yml file
```bash
conda env create -f environment.yml
```

### Activating the enviroment
```bash
conda activate ocp-env
```
## Class Shape Transformations 
- The CST method allows us to model a fully parameterized airfoil shape \(y(x)\) as the product of a **class function** \(C(x)\) and a **shape function** \(S(x)\).
- The shape coefficients determine the local behavior of the airfoil surface at each control point. In this implementation, we use six upper and six lower shape coefficients, allowing independent control over the thickness distribution of the upper and lower surfaces, respectively.

### Class Function

Defines the general class of shape (e.g., airfoils, flat plates, etc.):

$$
C(x) = x^{N_1} (1 - x)^{N_2}
$$

- \(x\) is the normalized chordwise location \([0,1]\)
- \(N_1\) and \(N_2\) are shape parameters controlling leading and trailing edge behavior

### Shape Function

Typically represented by a Bernstein polynomial expansion:

$$
S(x) = \sum_{i=0}^{n} A_i \, B_{i,n}(x)
$$

where

$$
B_{i,n}(x) = \binom{n}{i} x^{i} (1 - x)^{n - i}
$$

- \(A_i\) are the shape coefficients (control points)
- \(B_{i,n}(x)\) is the Bernstein basis polynomial of degree \(n\)

### Full Expression

Combining these gives the CST shape:

$$
y(x) = x^{N_1} (1 - x)^{N_2} \sum_{i=0}^n A_i \binom{n}{i} x^{i} (1 - x)^{n - i}
$$
