import argparse
import asyncio
import logging

from surrortg import ApiClient, get_config

DEFAULT_CONFIG_PATH = "/etc/srtg/srtg.toml"

parser = argparse.ArgumentParser()
parser.add_argument(
    "url", help="Current local url - this will be set to admin panel"
)
parser.add_argument("-c", "--config", default=DEFAULT_CONFIG_PATH)

args = parser.parse_args()

logging.getLogger().setLevel(logging.INFO)

config = get_config(args.config)

ge_config = config["game_engine"]

api_client = ApiClient(
    config["device_id"],
    ge_config["url"],
    ge_config["id"],
    ge_config["token"],
)

loop = asyncio.get_event_loop()
loop.run_until_complete(api_client.connect())
loop.run_until_complete(api_client.set_local_url(args.url))
