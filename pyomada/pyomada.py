from pathlib import Path
from typing import List, Union
from datetime import datetime
import logging
import json
import getpass

import requests
import yaml
import pandas as pd

# show all logs
logging.basicConfig(level=logging.DEBUG)

# set log level from requests and urllib3 to INFO
logging.getLogger("requests").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)


class OmadaAPI:

    def __init__(self,
                 config_fpath: Path = Path("config.yml"),
                 baseurl: str = "https://omadacontroller.local:8043",
                 site: str = "Default",
                 verify: bool = True,
                 debug: bool = True):

        self.config_fpath = Path(config_fpath)
        self.token = None
        self.base_api_path = "/api/v2"

        self.debug = debug

        if self.config_fpath.is_file():
            self.config_dict = self.read_yml(self.config_fpath)
            self.baseurl = self.config_dict["baseurl"]
            self.site = self.config_dict["site"]
            self.verify = self.config_dict["verify"]

            self.login_username = self.config_dict["username"]
            self.login_password = self.config_dict["password"]
        else:
            self.baseurl = baseurl
            self.site = site
            self.verify = verify

            self.login_username, self.login_password = self.login_prompt()

        self.session = requests.Session()
        self.session.verify = self.verify

        # if verification is disabled, disable the warning
        if not self.verify:
            requests.packages.urllib3.disable_warnings()

    @staticmethod
    def read_yml(yml_fpath: Path):
        """read a yml config file"""
        with yml_fpath.open(mode="r") as infile:
            cfg = yaml.load(infile, Loader=yaml.FullLoader)
        return cfg

    @staticmethod
    def get_timestamp() -> int:
        return int(datetime.utcnow().timestamp() * 1000)

    def path_to_url(self, path: str):
        return self.baseurl + self.base_api_path + path

    def makeApiCall(self,
                    url: str = None,
                    mode: str = "GET",
                    endpoint_params: dict = None,
                    data: dict = None,
                    json: dict = None,
                    debug: bool = False,
                    include_token: bool = True,
                    bare_url: str = False,
                    serialize_result: bool = True,
                    ) -> Union[dict, requests.Response]:
        """
        make an API call to the Omada API
        :param serialize_result: whether to serialize the result
        :param json: the json to send
        :param data: the data to send
        :param url: the url to call
        :param mode: the HTTP method to use
        :param endpoint_params: the parameters to send to the endpoint
        :param debug: print the response
        :param include_token: include the token in the request
        :param bare_url: don't include the base url
        :return: the response
        """

        if endpoint_params is None:
            endpoint_params = {}

        if not bare_url:
            url = self.path_to_url(url)

        if include_token:
            endpoint_params.update({
                "token": self.token,
                "_": self.get_timestamp()
            })

        # print a request debug summary
        if self.debug:
            print(" -- REQUEST DEBUG SUMMARY --")
            print(f"{mode} {url}")
            if endpoint_params:
                print(f"endpoint_params: {endpoint_params}")
            if data:
                print(f"data: {data}")
            if json:
                print(f"json: {json}")

        if mode == "GET":
            data = self.session.get(url=url,
                                    params=endpoint_params)
        elif mode == "POST":
            data = self.session.post(url=url,
                                     params=endpoint_params,
                                     data=data,
                                     json=json)
        elif mode == "PATCH":
            data = self.session.patch(url=url,
                                      params=endpoint_params,
                                      data=data,
                                      json=json)
        else:
            raise ValueError(f"Unsupported mode {mode}")

        if serialize_result:
            # get the json response
            response = data.json()

            response = {
                "url": url,
                "endpoint_params": endpoint_params,
                "endpoint_params_pretty": self.safe_json_serialize(endpoint_params),
                "json_data": response,
                "json_data_pretty": self.safe_json_serialize(response)
            }

            if debug:
                print("-- REPONSE DEBUG SUMMARY --")
                # print(f"type: {mode}")
                # print(f"verify: {self.verify}")
                # print(f"url: {response['url']}")
                # print(f"endpoint params: {response['endpoint_params_pretty']}")
                print(f"json data: {response['json_data_pretty']}")
                print("\n")
            return response["json_data"]
        else:
            if debug:
                print("-- RESPONSE DEBUG SUMMARY --")
                print(f"response: {str(data)}")
                print("\n")
            return data

    @staticmethod
    def safe_json_serialize(obj, indent=4):
        """
        serialize an object to json, but don't fail if it can't be serialized
        :param obj: the object to serialize
        :param indent: the indentation level
        :return: the serialized object
        """

        return json.dumps(obj, default=lambda o: f"<<non-serializable: {type(o).__qualname__}>>")

    @staticmethod
    def login_prompt() -> (str, str):
        """
        prompt the user for login credentials
        :return: the username and password
        """

        login_username = input("Omada login:")
        login_password = getpass.getpass(prompt="password:")

        return login_username, login_password

    def login(self):
        """
        login to the Omada API
        :return: the token
        """

        json_dict = {
            "username": self.login_username,
            "password": self.login_password
        }
        result = self.makeApiCall(url="/login",
                                  json=json_dict,
                                  mode="POST",
                                  include_token=False,
                                  debug=self.debug)
        self.token = result["result"]["token"]
        return self.token

    def logout(self):
        """
        logout from the Omada API
        :return:
        """

        result = self.makeApiCall(url="/logout",
                                  mode="POST",
                                  include_token=False,
                                  serialize_result=False,
                                  debug=self.debug)
        status_code = result.status_code
        if status_code == 200:
            logging.info("logged out")
        else:
            logging.warning(f"logout failed with status code {status_code}")

    def is_logged(self):
        """
        check if the user is logged in
        :return: True if logged in, False otherwise
        """

        result = self.makeApiCall(url="/loginStatus",
                                  mode="GET",
                                  serialize_result=False,
                                  debug=True)
        status_code = result.status_code
        if status_code == 200:
            return True
        else:
            return False

    # get the list of admin accounts
    def get_admins(self) -> pd.DataFrame:
        """
        get the list of admin accounts
        :return: a pandas dataframe of the admins
        """

        result = self.makeApiCall(url="/users",
                                  mode="GET",
                                  serialize_result=True,
                                  debug=self.debug)
        return pd.DataFrame(result["result"]["data"])

    # get the list of sites
    def get_sites(self) -> pd.DataFrame:
        """
        get the list of sites
        :return: a pandas dataframe of the sites
        """

        result = self.makeApiCall(url="/sites",
                                  mode="GET",
                                  serialize_result=True,
                                  debug=self.debug)
        return pd.DataFrame(result["result"]["data"])

    # get the list of scenarios
    def get_scenarios(self) -> list:
        """
        get the list of scenarios
        :return: a pandas dataframe of the scenarios
        """

        result = self.makeApiCall(url="/scenarios",
                                  mode="GET",
                                  serialize_result=True,
                                  debug=self.debug)
        return result["result"]

    # get all settings of a site
    def get_site_settings(self, site_key: str) -> pd.DataFrame:
        """
        get all settings of a site
        :param site_key: the site key
        :return: a pandas dataframe of the settings
        """

        result = self.makeApiCall(url=f"/sites/{site_key}/setting",
                                  mode="GET",
                                  serialize_result=True,
                                  debug=self.debug)
        return pd.DataFrame(result["result"])

    # get the list of devices for a given site
    def get_devices(self, site_key: str = None) -> pd.DataFrame:
        """
        get the list of devices for a given site
        :param site_key: the site key
        :return: a pandas dataframe of the devices
        """
        if site_key is None:
            site_key = self.site

        result = self.makeApiCall(url=f"/sites/{site_key}/devices",
                                  mode="GET",
                                  serialize_result=True,
                                  debug=self.debug)
        return pd.DataFrame(result["result"])

    # get site eaps
    def get_eap_data(self,
                     eap_mac: str,
                     site_key: str = None) -> pd.Series:
        """
        get site eaps
        :param site_key: the site key
        :param eap_mac: the eap mac
        :return: a pandas dataframe of the site eaps
        """

        if site_key is None:
            site_key = self.site

        result = self.makeApiCall(url=f"/sites/{site_key}/eaps/{eap_mac}",
                                  mode="GET",
                                  serialize_result=True,
                                  debug=self.debug)

        return pd.Series(result["result"])

    # set led status for an EAP
    def set_eap_2g_radio(self,
                         eap_mac: str,
                         radio_status: bool,
                         site_key: str = None):
        """
        enable or disable 2G radio for an EAP
        :param site_key: the site key
        :param eap_mac: the eap mac
        :param radio_status: the radio status, True for enabled, False for disabled
        :return: the result of the api call
        """
        if site_key is None:
            site_key = self.site

        result = self.makeApiCall(url=f"/sites/{site_key}/eaps/{eap_mac}",
                                  mode="PATCH",
                                  json={"radioSetting2g": {"radioEnable": radio_status}},
                                  serialize_result=True,
                                  debug=self.debug)

        return result

    def set_eap_led_status(self,
                           eap_mac: str,
                           led_status: int,
                           site_key: str = None):
        """
        set led status for an EAP
        :param site_key: the site key
        :param eap_mac: the eap mac
        :param led_status: the led status, 0 for off, 1 for on, 2 for site default
        :return: the result of the api call
        """

        if site_key is None:
            site_key = self.site

        result = self.makeApiCall(url=f"/sites/{site_key}/eaps/{eap_mac}",
                                  mode="PATCH",
                                  json={"ledSetting": led_status},
                                  serialize_result=True,
                                  debug=self.debug)

        return result
    # enable or disable 2G radio for an EAP

    # enable or disable 5G radio for an EAP
    def set_eap_5g_radio(self,
                         eap_mac: str,
                         radio_status: bool,
                         site_key: str = None):
        """
        enable or disable 5G radio for an EAP
        :param site_key: the site key
        :param eap_mac: the eap mac
        :param radio_status: the radio status, True for enabled, False for disabled
        :return: the result of the api call
        """
        if site_key is None:
            site_key = self.site

        result = self.makeApiCall(url=f"/sites/{site_key}/eaps/{eap_mac}",
                                  mode="PATCH",
                                  json={"radioSetting5g": {"radioEnable": radio_status}},
                                  serialize_result=True,
                                  debug=self.debug)

        return result


if __name__ == "__main__":
    omada = OmadaAPI(config_fpath=Path("config.yml"),
                     debug=True)

    omada.login()
    admins = omada.get_admins()
    sites = omada.get_sites()
    scenarios = omada.get_scenarios()
    settings = omada.get_site_settings(site_key="Default")
    devices = omada.get_devices(site_key="Default")
    eap_data = omada.get_eap_data(site_key="Default", eap_mac=devices.iloc[0]["mac"])
    eap_macs = list(devices["mac"])

    for mac in eap_macs:
        omada.set_eap_led_status(site_key="Default", eap_mac=mac, led_status=1)
        omada.set_eap_2g_radio(site_key="Default", eap_mac=mac, radio_status=True)