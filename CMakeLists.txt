cmake_minimum_required(VERSION 3.5)

project(VentriculostomySurfaceCut)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/VentriculostomySurfaceCut")
set(EXTENSION_CATEGORY "IGT")
set(EXTENSION_CONTRIBUTORS "Longquan (SPL)")
set(EXTENSION_DESCRIPTION "This is for the surface polydata generation")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/VentriculostomySurfaceCut.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/VentriculostomySurfaceCut/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(VentriculostomySurfaceCut)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
