
def IdentifyData_dlg(self):   

        """Create an action to get coordinates from mouse clicks."""
        self.dlg = IdentifyDataDialog()  # Assuming you have a dialog for this action
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)

        # Get the vintages from the API
        vintages=load_vintages(apikey)
        layer_list = vintages
        self.dlg.comboBox_vintage.clear()
        self.dlg.comboBox_vintage.addItems(layer_list)

        layer_list = getlayersnames(apikey)
        self.dlg.comboBox_layer.clear()
        self.dlg.comboBox_layer.addItems(layer_list)

       
        
        # Reference to the map canvas
        canvas = self.iface.mapCanvas()

        # Create a map tool to emit points on mouse click
        self.pointTool = QgsMapToolEmitPoint(canvas)

        # Connect the signal to a custom slot to handle the clicked point
        self.pointTool.canvasClicked.connect(lambda point, button: self.display_point(canvas,
            point, self.dlg.comboBox_vintage.currentText(), self.dlg.comboBox_layer.currentText()))

        # Set the map tool to the canvas
        canvas.setMapTool(self.pointTool)

        if self.actionIdentifyData.isChecked():
            self.dlg.show()
            self.dlg.finished.connect(lambda: self.iface.mapCanvas().setMapTool(QgsMapToolEmitPoint(self.iface.mapCanvas())))
            self.dlg.finished.connect(lambda: self.actionIdentifyData.setChecked(False))
        else:
            self.dlg.close()
            # if this action dialog is closed, deactivate the action        

def load_geometry_result_OLD(self):
        self.dlg.progressBar.reset()
        if len(self.dlg.mapVlayersCb.currentText())>0:
            selected_layer_obj = self.dlg.mapVlayersCb.currentLayer()
            layer = self.iface.activeLayer()
            # Open attribute table of the active layer
            selected_vintage = self.dlg.comboBox_vintage.currentText()  # Get the selected vintage from the combo box vintage
            selected_layer = self.dlg.comboBox_layer.currentText()  # Get the selected layer from the combo box layer
            Define_Layer=processing.run("native:saveselectedfeatures", {'INPUT':layer,'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
            Define_Layer.updateExtents()
            Define_Layer.createSpatialIndex()
            
            # Get the name of selected_layer_obj
            if self.dlg.checkBox_selection.isChecked():
                resultName = selected_layer_obj.name()+f"_selection_{selected_layer}{selected_vintage}"
            else:
                resultName = selected_layer_obj.name()+f"_{selected_layer}{selected_vintage}"
            self.iface.setActiveLayer(selected_layer_obj)
            
            self.dlg.infoBox.setText(f"Loading geometry for {resultName} layer...")
            self.dlg.infoBox.setStyleSheet("color: black;")          

            ids= []  
                
            vector_tile_layer =load_fabricvectortilelayer(selected_vintage,selected_layer,apikey)
    
        
            feature_ids = [f.id() for f in Define_Layer.getFeatures()]  # Get all feature IDs
            for feature_id in feature_ids:
                Define_Layer.selectByIds([feature_id])
                box = Define_Layer.boundingBoxOfSelected()
                if not box.isNull():
                    # Set the extent of the map canvas to the bounding box of the selected features
                    self.iface.mapCanvas().setDestinationCrs(Define_Layer.crs())
                    self.iface.mapCanvas().setExtent(box)
                    self.iface.mapCanvas().refresh()
                geometry = Define_Layer.getGeometry(feature_id)
                context = QgsSelectionContext()
                canvas = self.iface.mapCanvas()
                context.setScale(canvas.scale())
                xform = QgsCoordinateTransform(Define_Layer.crs(), vector_tile_layer.crs(), QgsProject.instance())
                geometry.transform(xform)
                vector_tile_layer.selectByGeometry(
                    geometry,
                    context)
                if selected_layer != "locations":
                    layer = QgsVectorLayer("Polygon?crs="+vector_tile_layer.crs().authid()+"&field=uuid:string(255)", f"{resultName}", "memory")
                    layer.startEditing()
                    for feature in vector_tile_layer.selectedFeatures():
                        newfeature = QgsFeature()
                        tilegeom=feature.geometry()
                        newfeature.setGeometry(tilegeom)
                        uuid=feature.attributes()[0]
                        newfeature.setAttributes([uuid])
                        layer.dataProvider().addFeatures([newfeature])
                        
                        ids.append(uuid)
                    layer.commitChanges()
                    # Create a new GeoJSON file with the UUIDs
                    uuidjson_file = os.path.join(temp_dir, "selected_uuids.json")
                    # Create a new GeoJSON file with the UUIDs
                    with open(uuidjson_file, "w") as f:
                        json.dump(ids, f, indent=2)
                else:
                    for feature in vector_tile_layer.selectedFeatures(): 
                        uuid=feature.attributes()[0]
                        ids.append(uuid)
                        
                    # Create a new GeoJSON file with the UUIDs
                    uuidjson_file = os.path.join(temp_dir, "selected_uuids.json")
                    # Create a new GeoJSON file with the UUIDs
                    with open(uuidjson_file, "w") as f:
                        json.dump(ids, f, indent=2)
                    try:    
                            combined_data = bulk(uuidjson_file,['latitude','longitude'],selected_vintage,"locations",apikey,self.dlg.progressBar)
                            output_file = os.path.join(temp_dir, "selected_locations.csv")
                            with open(output_file, mode="w", newline="") as file:
                            # Get all keys from the first inner dictionary (assuming all dictionaries have the same structure)
                                fieldnames = list(next(iter(combined_data.values())).keys())
                                writer = csv.DictWriter(file, fieldnames=fieldnames)
                                
                                # Write the header
                                writer.writeheader()
                                
                                # Write each inner dictionary as a row
                                for inner_dict in combined_data.values():
                                    writer.writerow(inner_dict)

                            # Convert the CSV file to a shapefile
                            layer = processing.run("native:createpointslayerfromtable", {
                                'INPUT': output_file,
                                'XFIELD': 'longitude',
                                'YFIELD': 'latitude',
                                'ZFIELD': '',
                                'MFIELD': '',
                                'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
                                'OUTPUT': 'TEMPORARY_OUTPUT'
                            })['OUTPUT']

                        
                    except Exception as e:
                        self.iface.messageBar().pushMessage("Error", f"An error occurred: {str(e)}", level=Qgis.Critical)
                        return False

            # Get the list of fields from selectedFeaturesLw list widget
            selected_fields = []
            if self.dlg.selectedFeaturesLw.count() > 0:
                for i in range(self.dlg.selectedFeaturesLw.count()):
                    item = self.dlg.selectedFeaturesLw.item(i)
                    retrieved_data = item.data(QtCore.Qt.UserRole)
                    selected_fields.append(retrieved_data)
            
                combined_data = bulk(uuidjson_file,selected_fields,selected_vintage,selected_layer,apikey,self.dlg.progressBar)
                # Convert data to CSV file
                DateStamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                csvoutput_file = os.path.join(temp_dir, f"{resultName}_{DateStamp}.csv")
                
                with open(csvoutput_file, mode="w", newline="") as file:
                    
                # Get all keys from the first inner dictionary (assuming all dictionaries have the same structure)
                    fieldnames = list(next(iter(combined_data.values())).keys())
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    
                    # Write the header
                    writer.writeheader()
                    
                    # Write each inner dictionary as a row
                    for inner_dict in combined_data.values():
                        writer.writerow(inner_dict)
                
            
                joinshp=processing.run("native:joinattributestable", {'INPUT':layer,'FIELD':'uuid','INPUT_2':csvoutput_file,'FIELD_2':'uuid','FIELDS_TO_COPY':[],'METHOD':1,'DISCARD_NONMATCHING':False,'PREFIX':'','OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
                joinshp.setName(resultName)
                QgsProject.instance().addMapLayer(joinshp)
                self.dlg.infoBox.setText(f"{resultName}" + " layer with selected fields added to the map.")
                self.dlg.infoBox.setStyleSheet("color: green;")
            else:
                QgsProject.instance().addMapLayer(layer)
                self.dlg.infoBox.setText(f"{resultName}" + " layer with uuid added to the map.")
                self.dlg.infoBox.setStyleSheet("color: green;")
            # Update the progress bar to 100%
            self.dlg.progressBar.setFormat("Completed")
        else:
            self.dlg.infoBox.setText("Please select a define layer")
            self.dlg.infoBox.setStyleSheet("color: red;")
                # Change label_layer_3 to red and bold
            self.dlg.label_layer_3.setStyleSheet("color: red; font-weight: bold;")
            QApplication.processEvents()



def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = CQAFabricDialog()

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
    

def IdentifyData_1(self):  
        # get the current active layer every time when the active layer is changed
        
        if self.actionIdentifyData_1.isChecked():
            # get the uri of the layer


            # Reference to the map canvas
            canvas = self.iface.mapCanvas()
            
            # Create a map tool to emit points on mouse click
            self.pointTool = QgsMapToolEmitPoint(canvas)
                
            # Connect the signal to a custom slot to handle the clicked point
            self.pointTool.canvasClicked.connect(lambda point, button: self.onFeatureIdentified(point))
            # Convert point from QgsPointXY to geometry
            

            # Set the map tool to the canvas
            canvas.setMapTool(self.pointTool)
        
        else:
            self.iface.mapCanvas().setMapTool(QgsMapToolEmitPoint(self.iface.mapCanvas()))   
              
        
def onFeatureIdentified(self,point):
        # Create an identify tool
        identify_tool = QgsMapToolIdentify(self.iface.mapCanvas())
        # Perform the identification
        point_geom = QgsGeometry.fromPointXY(point)
        results = identify_tool.identify(point, QgsMapToolIdentify.TopDownStopAtFirst, [self.iface.activeLayer()])

        # Process the results
        for result in results:
            print(result.mFeature.attributes())   
            print("feature selected")  





def bulk(uuidjson,fieldlist,selected_vintage,selected_layer,apikey,progressbar=None):
    # Create the URL for the API request
    # reset the progress bar
    if progressbar is not None:
        progressbar.reset()
    with open(uuidjson, 'r') as f:
        data = json.load(f)
    
    total_records = len(data)
    total_fields = len(fieldlist)

    # Get the data level to determine Number of fields to process at a time
    url = f"https://api.costquest.com/accesscontrol/getaccess?userid={apikey}"
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req)
    response_data = json.loads(response.read())
    datalevel = response_data['info']['datalevel']

    batch_size = 1000  # Number of records to process at a time

    # Number of fields to process at a time
    if datalevel == 100:
        field_size = 25   
    else:
        field_size = 5  

    hdr ={
        # Request headers
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'apikey': apikey,
        }
    
    combined_data = []
    for start_1 in range(0, total_fields, field_size):
        fieldlist_sub = fieldlist[start_1:start_1 + field_size]
        url = f"https://costquest.azure-api.net/fabric/{selected_vintage}/bulk/{selected_layer}?field=" + ",".join(fieldlist_sub)

        for start in range(0, total_records, batch_size):
            # Get the current batch of records
            batch = data[start:start + batch_size]

            req = urllib.request.Request(url, headers=hdr, data=json.dumps(batch).encode('utf-8'))

            req.get_method = lambda: 'POST'
            response = urllib.request.urlopen(req)
            response_data = json.loads(response.read())
            combined_data.extend(response_data)
            # Update the progress bar if provided
            if progressbar:
                progressbar.setValue(progressbar.value() + int(start / total_records * (100-progressbar.value())))
                progressbar.update()
        
        # join the data by uuid
        combined_data_dict = {}
        for item in combined_data:
            if isinstance(item, dict):
                uuid = item.get("uuid")
                if uuid not in combined_data_dict:
                    combined_data_dict[uuid] = {}
                combined_data_dict[uuid].update(item)
    if progressbar:
        progressbar.setValue(100)
        progressbar.update()
    return combined_data_dict
    


def collect(geojson,selected_vintage,apikey):
    global ids
    global collect_calls
    global divide_calls
    # if collect_calls is not defined, initialize it
    if 'collect_calls' not in globals():
        collect_calls = 0
        divide_calls = 0
        ids = []            
    collect_calls += 1
    collect_ids = requests.post(baseuri + "fabric/" + selected_vintage + "/collect", json=geojson, headers={"apikey": apikey}).json()
    if len(collect_ids)>=5000:
        divide_results = requests.post(baseuri + "geosvc/divide", json=geojson, headers={"apikey": apikey}).json()
        for db in divide_results:
            divide_calls += 1
            print("divide " + str(divide_calls))
            collect(geojson,selected_vintage,apikey)
    else:
        print("adding " + str(len(collect_ids)) + " ids")
        ids = ids + collect_ids
    return ids


def summarizefabricloc(geojson,selected_vintage,fieldlist,apikey):
    try:
        url = f"https://api.costquest.com/testing/{selected_vintage}/summarize?field="+",".join(fieldlist)


        hdr ={
        # Request headers
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'apikey': apikey,
        }

        # Request body
        data = json.dumps(geojson)
        req = urllib.request.Request(url, headers=hdr, data = bytes(data.encode("utf-8")))

        req.get_method = lambda: 'POST'
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        if response.getcode() == 200:
            return data
    except Exception as e:
        print(e)
