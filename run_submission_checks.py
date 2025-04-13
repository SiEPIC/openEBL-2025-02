import pya
from pya import *
import SiEPIC
from SiEPIC.verification import layout_check
from SiEPIC.scripts import zoom_out
from SiEPIC.utils import get_technology_by_name
import siepic_ebeam_pdk
import os
import sys
"""
Script to load .gds file passed in through commmand line and run submission checks:
- layout floorplan dimensions
- number of top cells
- check for Black box cells

Jasmina Brar 12/08/23, and Lukas Chrostowski, 2025/02

"""

# Allowed BB cells:
bb_cells = [
        'ebeam_gc_te1550',
        'ebeam_gc_tm1550',
        'GC_TE_1550_8degOxide_BB', 
        'GC_TM_1550_8degOxide_BB', 
        'ebeam_gc_te1310', 
        'ebeam_gc_te1310_8deg', 
        'GC_TE_1310_8degOxide_BB', 
        'ebeam_GC_TM_1310_8degOxide',
        'GC_TM_1310_8degOxide_BB',
        'GC_TM_1310_8degOxide_BB$1', 
        'ebeam_splitter_swg_assist_te1310', 
        'ebeam_splitter_swg_assist_te1550',
        'ebeam_dream_splitter_1x2_te1550_BB',
]


# gds file to run verification on
gds_file = sys.argv[1]

print('')
print('')
print('')
print('')
print('Running submission checks for file %s' % gds_file)


from SiEPIC.scripts import replace_cell, cells_containing_bb_layers    


try:
   # load into layout
   layout = pya.Layout()
   layout.read(gds_file)
   num_errors = 0
   
except:
   print('Error loading layout')
   num_errors = 1

try:
   # get top cell from layout
   if len(layout.top_cells()) != 1:
      print('Error: layout does not have 1 top cell. It has %s.' % len(layout.top_cells()))
      num_errors += 1

   top_cell = layout.top_cell()

   # set layout technology because the technology seems to be empty, and we cannot load the technology using TECHNOLOGY = get_technology() because this isn't GUI mode
   # refer to line 103 in layout_check()
   # tech = layout.technology()
   # print("Tech:", tech.name)
   layout.TECHNOLOGY = get_technology_by_name('EBeam')

   # Make sure layout extent fits within the allocated area.
   cell_Width = 605000
   cell_Height = 410000
   bbox = top_cell.bbox()
   if bbox.width() > cell_Width or bbox.height() > cell_Height:
      print('Error: Cell bounding box / extent (%s, %s) is larger than the maximum size of %s X %s microns' % (bbox.width()/1000, bbox.height()/1000, cell_Width/1000, cell_Height/1000) )
      num_errors += 1


   # Check black box cells, by replacing them with an empty cell, 
   # then checking if there are any BB geometries left over
   dummy_layout = pya.Layout()
   dummy_cell = dummy_layout.create_cell("dummy_cell")
   dummy_file = "dummy_cell.gds"
   dummy_cell.write(dummy_file)
   bb_count = 0
   print ('Performing Black Box cell replacement check')
   for i in range(len(bb_cells)):
      text_out, count, error = replace_cell(layout, 
            cell_x_name = bb_cells[i], 
            cell_y_name = dummy_cell.name, 
            cell_y_file = dummy_file, 
            Exact = False, RequiredCharacter='$',
            run_layout_diff = False,
            debug = False,)
      if count and count > 0:
         bb_count += count
         print(' - black box cell: %s' % bb_cells[i])
   print (' - Number of black box cells to be replaced: %s' % bb_count)

   cells_bb = cells_containing_bb_layers(top_cell, BB_layerinfo=pya.LayerInfo(998,0), verbose=False)
   print(' - Number of unreplaced BB cells: %s' % len(cells_bb))
   if len(cells_bb) > 0:
      print(' - Names of unreplaced BB cells: %s' % set(cells_bb))
      print('ERROR: unidentified black box cells. Please ensure that the design only uses cells contained in the PDK: https://github.com/SiEPIC/SiEPIC_EBeam_PDK. Also ensure that the cells have not been modified in any way (rotations, origin changes, resizing, renaming).')
   num_errors += len(cells_bb)

except:
   print('Runtime exception.')
   if num_errors == 0:
      num_errors = 1

# Print the result value to standard output
print(num_errors)

