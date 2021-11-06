# pyomada
This is a (very rudimentary) Python API for TP-Link Omada.

TP-Link Omada at this day has no official API documentation, so a bit of reverse engineering has to be done.



## Usage

```python
from pathlib import Path

from pyomada import OmadaAPI
api = OmadaAPI(config_path=Path("omada_config.yml")
api.login()

devices = api.get_devices()
```

The config yml should look like this:

```yaml
baseurl: https://omadacontroller.local:8043
site: Default
verify: false

username: my_username
password: my_secret_password
```
