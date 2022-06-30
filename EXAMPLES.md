# EXAMPLES

This document describes the example files included as part of the github repo. 

## The FEBio Model
There are currently three example FEBio models that users can use to try out the FEBioUncertainSCI tool. All three describe the same model, but with three different mesh densities. The three model files are:

- Model1.feb: low resolution mesh
- Model2.feb: medium resolution mesh
- Model3.feb: high resolution mesh

The example problem is a uni-axial tensile test of a neo-Hookean hyperelastic material. A rigid body is attached and a rigid prescribed displacement is applied.  

## The control file
In order to run the FEBioUncertainSCI tool, the user must prepare a control file that contains the parameters of the analysis. A detailed description of the structure of the control file is given in the [README.md](readme.md#4-control-file-structure) file. 

Two example control files are provided. They work with any of the provided FEBio model example files. 

- control.json: This example quantifies the sensitivity of the model's material parameters (Young's modulus E, and Poisson's ratio v) on the rigid body reaction force necessary to achieve the desired deformation.
- control2.json: This example extends the previous example and also quantifies the sensitivity of the material's 95th percentile stress and strain. This example will show that the sensitivity of the Young's modulus on the strain is zero, which makes sense given that this is a displacement-based model that will always produce the same strain regardless of the Young's modulus. 

