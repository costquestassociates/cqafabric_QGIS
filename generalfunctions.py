import requests
import json
import urllib.request
import urllib.parse
import os
import sys
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest

plugin_dir = os.path.dirname(__file__)
my_module_path = os.path.join(plugin_dir, "cqazapi-pytools") 
sys.path.append(my_module_path)
import importlib.util
spec = importlib.util.spec_from_file_location("cqazapi_pytools", os.path.join(my_module_path, "__init__.py"))
cqazapi_pytools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cqazapi_pytools)

from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsDataSourceUri, QgsSettings, QgsVectorTileLayer


baseuri = "https://api.costquest.com/"
_fields_metadata_cache = {}


def is_point_fabric_layer(layer_name):
    return layer_name in {"locations","retirements"}


def get_or_create_apikey_authcfg(apikey):
    """
    Store/reuse API key in QGIS auth DB and return authcfg id.
    Returns empty string if auth manager is unavailable or config cannot be stored.
    """
    if not apikey:
        return ""

    auth_manager = QgsApplication.authManager()
    if auth_manager is None:
        return ""

    def _as_ok(result):
        if isinstance(result, tuple):
            return bool(result[0]) if len(result) > 0 else False
        return bool(result)

    def _load_cfg(authcfg_id):
        cfg = QgsAuthMethodConfig()
        result = auth_manager.loadAuthenticationConfig(authcfg_id, cfg, True)
        if isinstance(result, tuple):
            ok = bool(result[0]) if len(result) > 0 else False
            if len(result) > 1 and isinstance(result[1], QgsAuthMethodConfig):
                cfg = result[1]
            return ok, cfg
        return bool(result), cfg

    def _authcfg_has_expected_apikey(authcfg_id, expected_apikey):
        req = QNetworkRequest(QUrl("https://api.costquest.com/fabric/vintages"))
        if not _as_ok(auth_manager.updateNetworkRequest(req, authcfg_id)):
            return False
        if not req.hasRawHeader(b"apikey"):
            return False
        return bytes(req.rawHeader(b"apikey")).decode("utf-8", errors="ignore") == expected_apikey

    settings = QgsSettings()
    settings_key = "cqafabric/authcfg_id"
    existing_authcfg = settings.value(settings_key, "", type=str)

    if existing_authcfg:
        load_ok, existing_cfg = _load_cfg(existing_authcfg)
        if load_ok and existing_cfg.method().lower() == "apiheader":
            if _authcfg_has_expected_apikey(existing_authcfg, apikey):
                return existing_authcfg
        settings.remove(settings_key)

    cfg = QgsAuthMethodConfig()
    cfg.setName("CQA Fabric API Key")
    cfg.setMethod("APIHeader")
    cfg.setConfigMap({
        "name": "apikey",
        "value": apikey,
    })

    store_result = auth_manager.storeAuthenticationConfig(cfg)
    if isinstance(store_result, tuple):
        store_ok = bool(store_result[0]) if len(store_result) > 0 else False
        if len(store_result) > 1 and isinstance(store_result[1], QgsAuthMethodConfig):
            cfg = store_result[1]
    else:
        store_ok = bool(store_result)

    if store_ok and cfg.id() and _authcfg_has_expected_apikey(cfg.id(), apikey):
        settings.setValue(settings_key, cfg.id())
        return cfg.id()

    return ""




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
    url = "https://api.costquest.com/fabric/vintages"

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
        vintages.sort(reverse=True)  # Sort vintages in descending order
        return vintages
    else:
        print("Failed to fetch vintages. HTTP Code:", response.getcode())




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



def load_fabricvectortilelayer(selected_vintage,selected_layer,apikey):
    vector_tile_url = f"https://api.costquest.com/fabric/{selected_vintage}/tiles/{selected_layer}/{{z}}/{{x}}/{{y}}"
    styleUrl = f"https://cqazapihttp.blob.core.windows.net/$web/fabricstyles.json"
    # Create a QgsDataSourceUri object
    uri = QgsDataSourceUri()

    # Set the required parameters
    uri.setParam("styleUrl", styleUrl)  # Style URL
    uri.setParam("type", "xyz")  # Style URL
    uri.setParam("url", vector_tile_url)  # Base URL with placeholders
    uri.setParam("zmax", "14")  # Maximum zoom level
    if is_point_fabric_layer(selected_layer):
        uri.setParam("zmin", "0")  # Minimum zoom level
    else:
        uri.setParam("zmin", "12")
    # Prefer authcfg so API key is not serialized into layer source.
    authcfg_id = get_or_create_apikey_authcfg(apikey)
    if authcfg_id:
        uri.setParam("authcfg", authcfg_id)
    else:
        # Fallback for environments where APIHeader auth method is unavailable.
        uri.setParam("http-header:apikey",apikey)  # API key for authentication
    uri.setParam("http-header:Cache-Control", "no-cache")  # Cache control header

    # Encode the URI
    encoded_uri = uri.encodedUri().data().decode()
    #self.iface.messageBar().pushMessage("Message", encoded_uri, level=Qgis.Info)
    # Create the vector tile layer
    vector_tile_layer = QgsVectorTileLayer(encoded_uri, f"Fabric {selected_vintage} - {selected_layer}")
    
    # Set scale dependent visibility
    vector_tile_layer.setScaleBasedVisibility(True)
    if is_point_fabric_layer(selected_layer):
        # Visible from all scales
        vector_tile_layer.setMinimumScale(0)
        vector_tile_layer.setMaximumScale(0)  # 1:20,000
    else:
        # Only visible when zoomed in (e.g., between 1:10,000,000 and 1:100,000)
        vector_tile_layer.setMinimumScale(80000)  # 1:80,000
        vector_tile_layer.setMaximumScale(0)    # 1:20,000

    return vector_tile_layer

def collect_attach(selected_vintage, geojsonfile, fieldlist, apikey):
    cp = cqazapi_pytools.cqazapipytools(apikey)
    with open(geojsonfile, 'r') as f:
        geojson = json.loads(f.read())
    ids = cp.collect(selected_vintage, geojson)
    combined_data = cp.attach(selected_vintage, ids, fieldlist)
    return combined_data

def attach(selected_vintage,selected_layer, ids, fieldlist, apikey):
    cp = cqazapi_pytools.cqazapipytools(apikey)
    combined_data = cp.attach(selected_vintage, ids, fieldlist,layer=selected_layer)
    return combined_data


def individualdata(selected_vintage,selected_layer,apikey,uuid):
    if not selected_vintage or not selected_layer: 
            return []
    url = f"https://api.costquest.com/fabric/{selected_vintage}/data/{selected_layer}?uuid={uuid}"

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


def _getfieldsmetadata(vintage, layer, apikey):
    if not vintage or not layer:
        return []

    cache_key = (apikey, vintage, layer)
    if cache_key in _fields_metadata_cache:
        return _fields_metadata_cache[cache_key]

    url = f"https://api.costquest.com/fabric/{vintage}/fields/{layer}"
    headers = {'Cache-Control': 'no-cache', 'apikey': apikey}
    for attempt in range(4):
        try:
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                _fields_metadata_cache[cache_key] = data
                return data
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get('Retry-After', '5')
                try:
                    delay = max(1, int(retry_after))
                except (TypeError, ValueError):
                    delay = 5
                time.sleep(min(delay, 60))
                continue
            print(f"Failed to fetch fields information. HTTP Code: {response.status_code}")
            return []
        except requests.RequestException as exception:
            if attempt == 3:
                print(exception)
                return []
            time.sleep(2 ** attempt)
    return []


def getfieldsinfo(vintage: str, layer: str, apikey):
    return [
        item.get('fieldname')
        for item in _getfieldsmetadata(vintage, layer, apikey)
        if isinstance(item, dict) and item.get('fieldname')
    ]


def getfieldsdisplayname(vintage: str, layer: str, apikey):
    data = [
        item for item in _getfieldsmetadata(vintage, layer, apikey)
        if isinstance(item, dict)
    ]
    data.sort(key=lambda item: item.get('listorder') or 0, reverse=True)
    return {
        item.get('fieldname'): item.get('displayname') or item.get('fieldname')
        for item in data
        if isinstance(item, dict) and item.get('fieldname')
    }



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

def matchautocomplete(apikey, address,vintage):
    try:
        # replace spaces with %20 for URL encoding
        address = address.replace(" ", "%20")
        url = f"https://api.costquest.com/fabricext/{vintage}/match?text={address}"

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


def matchfabric(apikey, vintage, sourcedata):
    """Match address records using the API client's chunking and retry logic."""
    try:
        with cqazapi_pytools.cqazapipytools(apikey) as cp:
            return cp.match(vintage, sourcedata)
    except Exception as e:
        print(e)
        return None
    

def matchstructured(apikey, house_number,road, city, state,  postcode, vintage):
    try:
        url = f"https://api.costquest.com/fabricext/{vintage}/match?house_number={house_number}&road={road}&city={city}&state={state}&postalcode={postcode}".replace(" ", "%20")

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
    
def locatefabric(apikey, vintage, sourcedata, neardistancem=None):
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
        with cqazapi_pytools.cqazapipytools(apikey) as cp:
            return cp.locate(vintage, sourcedata, neardistancem=neardistancem)
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
    
