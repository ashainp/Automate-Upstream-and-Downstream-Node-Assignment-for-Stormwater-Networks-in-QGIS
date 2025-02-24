from qgis.core import *
from qgis.utils import iface

# Layers - Updated based on your input
pipes_layer = QgsProject.instance().mapLayersByName('Merged SW Lines')[0]
pits_layer = QgsProject.instance().mapLayersByName('Merged SW points')[0]

# Ensure editing mode for pipes
pipes_layer.startEditing()

# Create spatial index for pits for faster nearest neighbor search
index = QgsSpatialIndex(pits_layer.getFeatures())

# Get pit elevations and IDs in a dictionary {fid: (AssetID, elevation, point)}
pits_data = {}
for pit in pits_layer.getFeatures():
    pit_id = pit['AssetID']  # Updated field for Node ID
    elevation = pit['DEM value1']  # Updated elevation field
    pits_data[pit.id()] = (pit_id, elevation, pit.geometry().asPoint())

# Add US_NODE_ID and DS_NODE_ID fields if they don't exist
provider = pipes_layer.dataProvider()
if 'US_NODE_ID' not in [field.name() for field in provider.fields()]:
    provider.addAttributes([QgsField('US_NODE_ID', QVariant.String)])
if 'DS_NODE_ID' not in [field.name() for field in provider.fields()]:
    provider.addAttributes([QgsField('DS_NODE_ID', QVariant.String)])
pipes_layer.updateFields()

# Process each pipe
for pipe in pipes_layer.getFeatures():
    geom = pipe.geometry()
    start_point = geom.interpolate(0).asPoint()  # Start point of the line
    end_point = geom.interpolate(geom.length()).asPoint()  # End point of the line

    # Find nearest pit to start point
    nearest_start_fid = index.nearestNeighbor(start_point, 1)[0]
    start_id, start_elev, _ = pits_data[nearest_start_fid]

    # Find nearest pit to end point
    nearest_end_fid = index.nearestNeighbor(end_point, 1)[0]
    end_id, end_elev, _ = pits_data[nearest_end_fid]

    # Determine US and DS based on elevation
    if start_elev >= end_elev:
        us_id, ds_id = start_id, end_id
    else:
        us_id, ds_id = end_id, start_id

    # Update attributes
    pipes_layer.changeAttributeValue(pipe.id(), provider.fieldNameIndex('US_NODE_ID'), us_id)
    pipes_layer.changeAttributeValue(pipe.id(), provider.fieldNameIndex('DS_NODE_ID'), ds_id)

# Commit changes
pipes_layer.commitChanges()
print("✅ Upstream and downstream node IDs assigned successfully based on DEM elevations.")
