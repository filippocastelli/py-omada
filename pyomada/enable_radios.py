from pathlib import Path
from argparse import ArgumentParser
import logging

from pyomada import OmadaAPI


def main():
    """
    Main function
    """
    parser = ArgumentParser(description="Enable radios on all devices")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug output")
    parser.add_argument("-c", "--config", type=str,
                        default="config.yml",
                        help="Path to config file")
    parser.add_argument("-d", "--disable",
                        action="store_true",
                        help="Disable radios")
    parser.add_argument("--no-leds",
                        dest="noleds",
                        action="store_true",
                        help="ignore leds")

    args = parser.parse_args()

    cfg_path = Path(args.config)
    api = OmadaAPI(config_fpath=cfg_path,
                   debug=args.verbose)
    api.login()

    devices = api.get_devices()
    device_macs = list(devices["mac"])

    # if status is true, enable radios and enable led, else disable radios and disable led
    if not args.disable:
        radio_status = True
        led_status = 1
        enabling_str = "enabling"
    else:
        radio_status = False
        led_status = 0
        enabling_str = "disabling"

    for df_id, df_row in devices.iterrows():
        mac_address = df_row["mac"]
        device_name = df_row["name"]

        logging.info(f"{enabling_str} radios on {device_name} ({mac_address})")
        api.set_eap_2g_radio(eap_mac=mac_address,
                             radio_status=radio_status)
        
        if not args.noleds:
            logging.info(f"{enabling_str} led on {device_name} ({mac_address})")
            api.set_eap_led_status(eap_mac=mac_address,
                                led_status=led_status)


if __name__ == "__main__":
    main()
