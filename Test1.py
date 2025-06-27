import requests
import json
import urllib.request

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
        else:
            print("Failed to fetch address. HTTP Code:", response.getcode())
            return None   
    except Exception as e:
        print(e)
        return None


def locatefabric(apikey, vintage, origdata):
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
        data = json.dumps(origdata)
        req = urllib.request.Request(url, headers=hdr, data = bytes(data.encode("utf-8")))

        req.get_method = lambda: 'POST'
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            result = json.loads(response.read())
            return result   
    except Exception as e:
        print("Failed to locate fabric.")
        result = []
        for dic in origdata:
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
        print(result) 
    
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

def translatefabric(apikey, vintage, id, src, dest):
    if not src:
        src= "location_id"
    if not dest:
        dest= "uuid"
    try:
        url = f"https://api.costquest.com/fabricext/{vintage}/translate?id={id}&src={src}&dst={dest}"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'apikey': apikey,
        }

        req = urllib.request.Request(url, headers=hdr)

        req.get_method = lambda: 'GET'
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            result = json.loads(response.read())
            return result
        else:
            print("Failed to fetch address. HTTP Code:", response.getcode())
            return None   
    except Exception as e:
        print(e)
        return None
    '''
    [{
    "uuid": "affc4405-eb13-41cf-afa4-2b5142b95338",
    "location_id": 1340235422
    }]'''

apikey = 'cq-4601df7497bb9ce596c5eb8f197b90a8'

data = geocodeautocomplete(apikey, '518 Riddle')

if data:
    for key, value in data.items():
        coordinates = None
        if key == "features":
            coordinates_data = []
            for item in value:
                coordinates =item['geometry']['coordinates']
                sourcekey = item['properties']['id']
                # Create a list of dictionaries with latitude and longitude
                coordinates_data.append({
                    "latitude": coordinates[1],
                    "longitude": coordinates[0],
                    "sourcekey": sourcekey
                    })
    

data_1 = locatefabric(apikey, '202406', coordinates_data)


if data_1:
    location_id = [item.get('location_id') for item in data_1 if isinstance(item, dict)]

