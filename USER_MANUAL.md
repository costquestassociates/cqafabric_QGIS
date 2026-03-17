# CQAFABRIC_QGIS User Manual

## Overview

`CQAFABRIC_QGIS` is a QGIS plugin for working with CostQuest CQA Fabric data through the CostQuest APIs.

The plugin provides six main workflows:

- `Log In` to store and reuse your API key
- `Add Fabric Tiles` to add Fabric layers to the map or the QGIS Browser
- `Retrieve Fabric` to pull attribute data for an area of interest
- `Identify Fabric` to click a Fabric feature and inspect its attributes
- `Locate Fabric` to find Fabric locations from an address or coordinates

## Requirements

- QGIS 3.x
- A valid CostQuest API key
- Network access from QGIS to `api.costquest.com`

## Installation

1. Download the plugin ZIP package.
2. In QGIS, open `Plugins > Manage and Install Plugins...`.
3. Open the `Install from ZIP` tab.
4. Select the plugin ZIP and install it.
5. Enable `CQA Fabric` if QGIS does not enable it automatically.

## Getting Started

After installation, the plugin adds a `CQA Fabric` menu and toolbar in QGIS.

### Log In

1. Click `CQA Fabric > Log In`.
2. Enter your API key.
3. Click `Save`.

If the key is valid, the plugin enables the remaining tools and changes the button label to `Log Out`.

### Log Out

1. Click `CQA Fabric > Log Out`.
2. The saved key is removed and the login dialog is shown again.


## Add Fabric Tiles

Use this tool to add Fabric vector tiles to the current map or save a Fabric source in the QGIS Browser.

### Steps

1. Open `CQA Fabric > Add Fabric Tiles`.
2. Choose a `Vintage`.
3. Choose a `Layer`.
4. Click `Add Tiles to Map` to load the selected Fabric layer directly into the map, or click `Add Tiles Source` to save the selected Fabric layer as a reusable vector tile connection in the QGIS Browser.

### Notes

- `locations` is visible at all scales.
- Other Fabric layers are intended for closer zoom levels.
- If a layer fails to load, confirm that your API key is valid and that QGIS can reach the CostQuest API.

## Retrieve Fabric

Use this tool to retrieve Fabric attributes for a boundary layer in your project.

### What You Need

- A polygon layer in QGIS to define the area of interest
- At least one selected output field
- A valid Fabric `Vintage` and `Layer`

### Steps

1. Add or create a polygon layer in QGIS.
2. If you want to limit the request to part of that layer, preselect the polygons you want to use.
3. Open `CQA Fabric > Retrieve Fabric`.
4. Select the polygon boundary layer from the layer drop-down.
5. Choose the Fabric `Vintage`.
6. Choose the Fabric `Layer`.
7. Move one or more fields from `Available` to `Selected`.
8. Click the button to populate the result table.
9. Review the returned records in the table.
10. Click `Save` to export the result.

### Selection Behavior

- If the selection-only checkbox is enabled, the plugin uses only the currently selected polygons in the boundary layer.
- If the selection-only checkbox is not enabled, the plugin selects all polygons in the boundary layer before running the request.

### Results

When the export finishes, the plugin adds output layers to the project:

- a geometry layer joined with the retrieved attributes
- a CSV table containing the retrieved records

### Notes

- For the `locations` layer, the plugin dissolves the area of interest and uses the Fabric collect/attach workflow.
- For non-location layers, the plugin selects features from the vector tile layer by geometry and then retrieves attributes.
- Large areas may take time to process. The dialog prevents accidental closure while background tasks are running.

## Identify Fabric

Use this tool to click a Fabric feature on the map and inspect its attributes.

### What You Need

- An active Fabric vector tile layer in the Layers panel

### Steps

1. Add a Fabric layer to the map with `Add Fabric Tiles`.
2. Make that Fabric layer the active layer in the Layers panel.
3. Open `CQA Fabric > Identify Fabric`.
4. Click a feature on the map canvas.
5. Review the attributes shown in the popup window.

### Notes

- For the `locations` layer, the plugin locates the nearest Fabric location to the clicked point and marks it on the map.
- For polygon-style Fabric layers, the plugin highlights the selected geometry before showing details.
- If no Fabric layer is active, the plugin shows an informational message instead of returning data.

## Locate Fabric

Use this tool to locate Fabric records from an address or from coordinates.

### Search Modes

- Single address
- Address CSV
- Single coordinate pair
- Coordinate CSV

### Address Search

1. Open `CQA Fabric > Locate Fabric`.
2. Select a `Vintage`.
3. Choose `Address`.
4. Enter a single-line address, or enable `CSV` mode and browse to a CSV file.
5. Click `Show`.

### Coordinate Search

1. Open `CQA Fabric > Locate Fabric`.
2. Select a `Vintage`.
3. Choose `Coordinates`.
4. Enter one coordinate pair as `latitude,longitude` or `longitude,latitude`, or enable `CSV` mode and browse to a CSV file.
5. Click `Show`.

### Attach Attributes

If the `Attach Attributes` option is enabled, the plugin retrieves Fabric attributes for the matched results and displays them in the table.

If the option is not enabled, the result table contains the locate results only.

### Export Behavior

- When CSV mode is used, the plugin enables `Save` so the results can be written back to a new CSV file.
- The exported CSV is also added to the QGIS project.

### Required CSV Columns

Column matching is case-insensitive.

#### Address CSV

```csv
sourcekey,address
1,1600 Pennsylvania Ave NW Washington DC 20500
2,2 15th St NW Washington DC 20024
```

#### Coordinate CSV

```csv
sourcekey,latitude,longitude
1,38.8977,-77.0365
2,38.8895,-77.0353
```

## Files Created by the Plugin

The plugin creates or uses the following local files:

- Saved API key configuration: `C:\Users\<your-user>\AppData\Roaming\QGIS\QGIS_CQAFabric.config`
- Temporary and demo files root folder: `C:\Users\<your-user>\AppData\Roaming\QGIS\Temp\`

## Troubleshooting

### API key cannot be verified

- Confirm that the API key is correct.
- Confirm that QGIS has internet access.
- Confirm that the CostQuest API endpoint is reachable from your machine.

### No layers appear in Retrieve Fabric

- The boundary layer selector only accepts polygon vector layers.
- Add a polygon layer to the project and make sure it is valid.

### No features selected

- If using selection-only mode in `Retrieve Fabric`, make sure you selected polygons in the boundary layer before running the tool.

### Identify Fabric says no active Fabric layer

- Activate a Fabric vector tile layer in the Layers panel before clicking the map.

### Locate Fabric CSV import fails

- Verify the required column names are present.
- Make sure the CSV file is readable and uses standard comma-separated formatting.


## Support

For API key access or product support, contact CostQuest support through the channels used by your organization.
