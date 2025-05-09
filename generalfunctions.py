import requests
import json
import urllib.request
from qgis.core import QgsDataSourceUri, QgsVectorTileLayer
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtGui import QStandardItemModel, QStandardItem


baseuri = "https://api.costquest.com/"


def verify_apikey(apikey):
    url = "https://api.costquest.com/accountcontrol/listkeys"

    hdr ={
    # Request headers
    'Cache-Control': 'no-cache',
    'apikey': apikey,
    }
    try:
        req = urllib.request.Request(url, headers=hdr)
        req.get_method = lambda: 'GET'
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            return True
        else:
            return False
    except Exception as e:
        return False


def load_vintages(apikey):
    url = "https://costquest.azure-api.net/fabric/vintages"

    hdr ={
    # Request headers
    'Cache-Control': 'no-cache',
    'apikey': apikey,
    }
    req = urllib.request.Request(url, headers=hdr)
    req.get_method = lambda: 'GET'
    response = urllib.request.urlopen(req)
    if response.getcode() == 200:
        data = json.loads(response.read())
        vintages = [item.get('vintage') for item in data if isinstance(item, dict)]
        return vintages
    else:
        print("Failed to fetch vintages. HTTP Code:", response.getcode())


def load_fabricvectortilelayer(selected_vintage,selected_layer,apikey):
    vector_tile_url = f"https://costquest.azure-api.net/fabric/{selected_vintage}/tiles/{selected_layer}/{{z}}/{{x}}/{{y}}"
    styleUrl = f"https://cqazapihttp.blob.core.windows.net/$web/fabricstyles.json"
    # Create a QgsDataSourceUri object
    uri = QgsDataSourceUri()

    # Set the required parameters
    uri.setParam("styleUrl", styleUrl)  # Style URL
    uri.setParam("type", "xyz")  # Style URL
    uri.setParam("url", vector_tile_url)  # Base URL with placeholders
    uri.setParam("zmax", "14")  # Maximum zoom level
    if selected_layer == "locations":
        uri.setParam("zmin", "0")  # Minimum zoom level
    else:
        uri.setParam("zmin", "12")
    uri.setParam("http-header:apikey",apikey)  # API key for authentication
    uri.setParam("http-header:Cache-Control", "no-cache")  # Cache control header

    # Encode the URI
    encoded_uri = uri.encodedUri().data().decode()
    #self.iface.messageBar().pushMessage("Message", encoded_uri, level=Qgis.Info)
    # Create the vector tile layer
    vector_tile_layer = QgsVectorTileLayer(encoded_uri, f"Fabric {selected_vintage} - {selected_layer}")
    return vector_tile_layer


def bulk(uuidjson,fieldlist,selected_vintage,selected_layer,apikey):
    # Create the URL for the API request
    hdr ={
    # Request headers
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'apikey': apikey,
    }

    # Request body
    # Read the JSON file
    with open(uuidjson, 'r') as f:
        data = json.load(f)
    batch_size = 1000  # Number of records to process at a time
    total_records = len(data)
    combined_data = []

    field_size = 5
    total_fields = len(fieldlist)
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
        
        # join the data by uuid
        combined_data_dict = {}
        for item in combined_data:
            if isinstance(item, dict):
                uuid = item.get("uuid")
                if uuid not in combined_data_dict:
                    combined_data_dict[uuid] = {}
                combined_data_dict[uuid].update(item)

    return combined_data_dict


def collect(geojson,selected_vintage):
    global ids
    global collect_calls
    global divide_calls
    collect_calls += 1
    collect_ids = requests.post(baseuri + "fabric/" + selected_vintage + "/collect", json=geojson, headers={"apikey": apikey}).json()
    if len(collect_ids)>=5000:
        divide_results = requests.post(baseuri + "geosvc/divide", json=geojson, headers={"apikey": apikey}).json()
        for db in divide_results:
            divide_calls += 1
            print("divide " + str(divide_calls))
            collect(geojson,selected_vintage)
    else:
        print("adding " + str(len(collect_ids)) + " ids")
        ids = ids + collect_ids


def individualdata(selected_vintage,selected_layer,apikey,uuid):
    url = f"https://costquest.azure-api.net/fabric/{selected_vintage}/data/{selected_layer}?uuid={uuid}"

    hdr ={
    # Request headers
    'Cache-Control': 'no-cache',
    'apikey': apikey,
    }

    req = urllib.request.Request(url, headers=hdr)

    req.get_method = lambda: 'GET'
    response = urllib.request.urlopen(req)
    if response.getcode() == 200:
        data = json.loads(response.read())
        return data
    else:
        print("Failed to fetch vintages. HTTP Code:", response.getcode())


def getfieldsinfo(vintage:str,layer:str,apikey):
        url = f"https://costquest.azure-api.net/fabric/{vintage}/fields/{layer}"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'apikey': apikey,
        }

        req = urllib.request.Request(url, headers=hdr)

        req.get_method = lambda: 'GET'
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            data = json.loads(response.read())
            # sort the data by listorder
            return data
            #fieldnames = [item.get('fieldname') for item in data if isinstance(item, dict)]

        else:
            print("Failed to fetch fields information. HTTP Code:", response.getcode())

def getlayersnames(apikey):
        url = f"https://api.costquest.com/fabric/layers"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'apikey': apikey,
        }

        req = urllib.request.Request(url, headers=hdr)

        req.get_method = lambda: 'GET'
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            data = json.loads(response.read())
            # sort the data by listorder
            layernames = [item.get('layername') for item in data if isinstance(item, dict)]
            return layernames

        else:
            print("Failed to fetch layer names. HTTP Code:", response.getcode())


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
        else:
            print("Failed to fetch vintages. HTTP Code:", response.getcode())
    except Exception as e:
        print(e)


def populate_table_result(table_view, data):
    """
    Populate the tableResult QTableView with data.

    :param table_view: The QTableView instance to populate.
    :param data: A list of dictionaries or a list of lists containing the data to display.
    """
    # Create a model for the table
    model = QStandardItemModel()

    # Check if data is empty
    if not data:
        table_view.setModel(model)
        return

    # Set headers (assuming data is a list of dictionaries)
    if isinstance(data[0], dict):
        headers = list(data[0].keys())
        model.setHorizontalHeaderLabels(headers)

        # Populate the table with data
        for row_data in data:
            row_items = [QStandardItem(str(row_data[key])) for key in headers]
            model.appendRow(row_items)
    else:
        # If data is a list of lists, populate directly
        for row_data in data:
            row_items = [QStandardItem(str(value)) for value in row_data]
            model.appendRow(row_items)

    # Set the model to the table view
    table_view.setModel(model)