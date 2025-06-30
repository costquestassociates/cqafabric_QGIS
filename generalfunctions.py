import requests
import json
import urllib.request
from qgis.core import QgsDataSourceUri, QgsVectorTileLayer


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
        field_size = total_fields   
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


def individualdata(selected_vintage,selected_layer,apikey,uuid):
    if not selected_vintage or not selected_layer: 
            return []
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
        if not vintage or not layer: 
            return []
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
            fieldnames = [item.get('fieldname') for item in data if isinstance(item, dict)]
            return fieldnames
        else:
            print("Failed to fetch fields information. HTTP Code:", response.getcode())


def getfieldsdisplayname(vintage:str,layer:str,apikey):   
        if not vintage or not layer: 
            return []  
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
            data.sort(key=lambda x: x.get('listorder') or 0, reverse=True)
            displynames_dict = {item.get('fieldname'): item.get('displayname') if item.get('displayname') else item.get('fieldname')  for item in data if isinstance(item, dict)}
            return displynames_dict
        else:
            print("Failed to fetch fieldname. HTTP Code:", response.getcode())


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
    except Exception as e:
        print(e)


def geocodeautocomplete(apikey, address):
    try:
        # replace spaces with %20 for URL encoding
        address = address.replace(" ", "%20")
        url = f"https://api.costquest.com/geocode/autocomplete?text={address}"

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
    except Exception as e:
        print(e)
        return None
    

def geocodestructured(apikey, address, city, state,  zipcode):
    try:
        url = f"https://api.costquest.com/geocode/search/structured?address={address}&locality={city}&region={state}&postalcode={zipcode}".replace(" ", "%20")

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
            print("Failed to fetch address. HTTP Code:", response.getcode())
            return None   
    except Exception as e:
        print(e)
        return None


def locatefabric(apikey, vintage, sourcedata):
    ''' example: 
    data = [{
    "latitude": 36.66057141,
    "longitude": -80.92493726,
    "sourcekey": 31729768
    }, {
    "latitude": 36.65604364,
    "longitude": -80.92737851,
    "sourcekey": 31730797
    }]
    '''
    try:
        url = f"https://api.costquest.com/fabricext/{vintage}/locate"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'apikey': apikey,
        }
        data = json.dumps(sourcedata)
        req = urllib.request.Request(url, headers=hdr, data = bytes(data.encode("utf-8")))

        req.get_method = lambda: 'POST'
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            result = json.loads(response.read())
            return result

               
    except Exception as e:
        try:
            result = []
            for dic in sourcedata:
                url = f"https://api.costquest.com/fabricext/{vintage}/locate?latitude={dic["latitude"]}&longitude={dic["longitude"]}"
                req = urllib.request.Request(url, headers=hdr)

                req.get_method = lambda: 'GET'
                response = urllib.request.urlopen(req)
                if response.getcode() == 200:
                    result_temp = json.loads(response.read())
                    # update the sourcekey in the result_temp
                    for dic_temp in result_temp:
                        dic_temp["sourcekey"] = dic["sourcekey"]
                    result.extend(result_temp)
                else:
                    result.append({"latitude": None, "distancem": None, "longitude": None, "matchtype": None, "sourcekey": dic["sourcekey"], "location_id": None})
            return result
        except Exception as e:
            print(e)
            return None
    
    '''example result = [{
        "latitude": 36.66057141,
        "distancem": 0,
        "longitude": -80.92493726,
        "matchtype": "FootprintParcel",
        "sourcekey": "31729768",
        "location_id": 1000009896
    }, {
        "latitude": 36.65604364,
        "distancem": 0,
        "longitude": -80.92737851,
        "matchtype": "FootprintParcel",
        "sourcekey": "31730797",
        "location_id": 1000008779
    }'''

def translatefabric(apikey, vintage, data, src, dest):
    if not src:
        src= "location_id"
    if not dest:
        dest= "uuid"
    try:
        url = f"https://api.costquest.com/fabricext/{vintage}/translate"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'apikey': apikey,
        }
        data = json.dumps(data)
        req = urllib.request.Request(url, headers=hdr, data = bytes(data.encode("utf-8")))

        req.get_method = lambda: 'POST'
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            result = json.loads(response.read())
            return result  
    except Exception as e:
        print(e)
        return None
    '''
    [{
    "uuid": "affc4405-eb13-41cf-afa4-2b5142b95338",
    "location_id": 1340235422
    }]'''
    