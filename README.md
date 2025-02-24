# 🌊 Auto-Assign Upstream & Downstream Nodes for Stormwater Networks in QGIS

This PyQGIS script **automatically assigns upstream (US_NODE_ID) and downstream (DS_NODE_ID) node IDs** to stormwater pipes based on the **elevation of connected pits**. It’s ideal for preparing datasets for **InfoWorks ICM** and other hydraulic modelling software that requires correct flow direction mapping.

---

## 🚀 Features
- ✅ Fully automated US/DS node assignment based on pit elevations.
- ✅ Uses **DEM data** to determine flow direction (higher elevation = upstream).
- ✅ Ready for **InfoWorks ICM** import with correctly mapped node fields.
- ✅ Handles large datasets efficiently using spatial indexing.
- ✅ No manual snapping or direction correction needed.

---

## 📂 Requirements
- **QGIS 3.x** with Python console access.
- A **pipes layer** (Line) and a **pits layer** (Point) with:
  - **Node ID field** (e.g., `AssetID`).
  - **Elevation field** (e.g., `DEM value1`).

---

## 🔧 How to Use

### 1️⃣ **Prepare Your Data in QGIS**
- Load your:
  - **Pipes layer** (e.g., `Merged SW Lines`).
  - **Pits layer** (e.g., `Merged SW points`) with elevation (`DEM value1`).

---

### 2️⃣ **Run the Script**
1. Open **QGIS** ➔ **Plugins** ➔ **Python Console** ➔ **Show Editor**.
2. **Copy & paste the script** (provided below).
3. Click **Run** (green arrow).  
4. The script will:
   - Identify nearest pits at both ends of each pipe.
   - Compare DEM elevations.
   - Assign **US_NODE_ID** (higher elevation pit) and **DS_NODE_ID** (lower elevation pit).
### ✏ **Customisation**

| **Parameter**        | **Description**                             | **Replace With**                        |
|----------------------|---------------------------------------------|------------------------------------------|
| `'Merged SW Lines'`  | Name of your **pipes** layer                 | Your pipes layer name                   |
| `'Merged SW points'` | Name of your **pits** layer                  | Your pits layer name                    |
| `'AssetID'`          | **Node ID** field in pits                    | Your node ID field                      |
| `'DEM value1'`       | **Elevation** field in pits                  | Your elevation field name               |

### 📝 **Example Output**

| Pipe_ID | US_NODE_ID | DS_NODE_ID | Diameter | Material |
|---------|-------------|-------------|----------|-----------|
| 101     | P1          | P5          | 450 mm   | uPVC      |
| 102     | P3          | P2          | 300 mm   | RC        |
| 103     | P7          | P4          | 375 mm   | Steel     |

### 🎯 **Why This Script is Useful**

- 🔄 **Eliminates Manual Work**: Automatically assigns node directions for large networks.
- ⚡ **Fast & Efficient**: Processes hundreds of pipes in seconds using spatial indexing.
- 🌍 **DEM-Based Accuracy**: Ensures flow direction matches natural elevation differences.
- 🏗 **Flood modelling software ready**: Output fields match InfoWorks ICM requirements for seamless imports.

---

### 💻 **The Script:**

```python
from qgis.core import *
from qgis.utils import iface

# Layers - Update these names if different in your QGIS project
pipes_layer = QgsProject.instance().mapLayersByName('Merged SW Lines')[0]
pits_layer = QgsProject.instance().mapLayersByName('Merged SW points')[0]

# Ensure editing mode for pipes
pipes_layer.startEditing()

# Create spatial index for faster processing
index = QgsSpatialIndex(pits_layer.getFeatures())

# Get pit elevations and IDs
pits_data = {}
for pit in pits_layer.getFeatures():
    pit_id = pit['AssetID']  # Node ID field
    elevation = pit['DEM value1']  # Elevation field
    pits_data[pit.id()] = (pit_id, elevation, pit.geometry().asPoint())

# Add fields if missing
provider = pipes_layer.dataProvider()
if 'US_NODE_ID' not in [field.name() for field in provider.fields()]:
    provider.addAttributes([QgsField('US_NODE_ID', QVariant.String)])
if 'DS_NODE_ID' not in [field.name() for field in provider.fields()]:
    provider.addAttributes([QgsField('DS_NODE_ID', QVariant.String)])
pipes_layer.updateFields()

# Assign US and DS nodes
for pipe in pipes_layer.getFeatures():
    geom = pipe.geometry()
    start_point = geom.interpolate(0).asPoint()
    end_point = geom.interpolate(geom.length()).asPoint()

    nearest_start_fid = index.nearestNeighbor(start_point, 1)[0]
    start_id, start_elev, _ = pits_data[nearest_start_fid]

    nearest_end_fid = index.nearestNeighbor(end_point, 1)[0]
    end_id, end_elev, _ = pits_data[nearest_end_fid]

    if start_elev >= end_elev:
        us_id, ds_id = start_id, end_id
    else:
        us_id, ds_id = end_id, start_id

    pipes_layer.changeAttributeValue(pipe.id(), provider.fieldNameIndex('US_NODE_ID'), us_id)
    pipes_layer.changeAttributeValue(pipe.id(), provider.fieldNameIndex('DS_NODE_ID'), ds_id)

# Commit changes
pipes_layer.commitChanges()
print("✅ Upstream and downstream node IDs assigned successfully.")

