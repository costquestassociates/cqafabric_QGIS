import os
import sys
import json

plugin_dir = os.path.dirname(__file__)
my_module_path = os.path.join(plugin_dir, "cqazapi-pytools") 
sys.path.append(my_module_path)
import importlib.util
spec = importlib.util.spec_from_file_location("cqazapi_pytools", os.path.join(my_module_path, "__init__.py"))
cqazapi_pytools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cqazapi_pytools)

uuidjson=r"C:\Users\hchen\AppData\Roaming\QGIS\Temp\selected_uuids.json"
with open(uuidjson, 'r') as f:
        data = json.load(f)
apikey ="cq-ebb88c8c4e08406d6f5a4e792ae0c164"
url = f"https://costquest.azure-api.net/fabric/202406/bulk/locations?field=fcc_rel"
cp = cqazapi_pytools.cqazapipytools(apikey)
response = cp.apiBulkAction(url, 'POST',data)
#response = cp.attach("202406",data, ['fcc_rel', 'location_id'])
print(response)