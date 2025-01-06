#!/usr/bin/env python3

"""
Small script that takes the following steps:
 - fetch current ipv4 address from ipify.org
 - fetch current record for given domain name from Porkbun API
 - if the ip addresses differ, update the DNS record at Porkbun API
"""
from __future__ import annotations

import argparse
import os
import sys
from argparse import Namespace
from ipaddress import IPv4Address
from typing import Any, Dict, Tuple

import requests

PORKBUN_API_URL = "https://api.porkbun.com/api/json/v3/dns"


def parse_args() -> argparse.Namespace:
    # use argparse to parse arguments
    parser = argparse.ArgumentParser(description='Dynamic DNS updater')
    parser.add_argument('domain', type=str, help='Base domain')
    parser.add_argument('host', type=str, help='Hostname within base domain to update')
    config = parser.parse_args()

    # read Porkbun API key and secret from the environment
    config.api_key = os.environ.get("PORKBUN_API_KEY")
    config.secret = os.environ.get("PORKBUN_SECRET")

    # check if the environment variables are set
    if not config.api_key or not config.secret:
        print("Please set the PORKBUN_API_KEY and PORKBUN_SECRET environment variables")
        sys.exit(1)

    return config


def get_my_ip() -> IPv4Address:
    # fetch the current ip address
    response = requests.get("https://api4.ipify.org?format=json")
    response.raise_for_status()
    return IPv4Address(response.json()["ip"])


def porkbun_request(config: Namespace,
                    operation: str, data: list[str] = None, param: Dict[str, Any] = None) -> Dict[str, Any]:
    body = param or {}
    # make a request to the Porkbun API
    body["apikey"] = config.api_key
    body["secretapikey"] = config.secret

    url = f"{PORKBUN_API_URL}/{operation}"
    if data:
        url += "/" + "/".join(data)

    response = requests.post(url, json=body)

    if response.status_code >= 500:
        response.raise_for_status()

    data = response.json()
    if data.get("status") != "SUCCESS":
        raise ValueError(f"Error in Porkbun API: {data['status']} - {data['message']}")

    return data


def get_dns_record(domain: str, hostname: str, config: Namespace) -> Tuple[IPv4Address | None, int | None]:
    # lookup the current DNS record for the given domain and hostname
    data = porkbun_request(config, 'retrieve', [domain])
    for record in data["records"]:
        if record["name"] == f"{hostname}.{domain}" and record["type"] == "A":
            return IPv4Address(record["content"]), record["id"]
    return None, None


def create_dns_record(ip: IPv4Address, config: Namespace) -> None:
    # create a new DNS record for the given domain and hostname
    porkbun_request(config, 'create', [config.domain], {
        "name": config.hostname,
        "type": "A",
        "content": str(ip),
        "ttl": 60
    })


def update_dns_record(ip: IPv4Address, record_id: int, config: Namespace) -> None:
    # update the DNS record for the given domain and hostname
    porkbun_request(config, 'edit', [config.domain, str(record_id)], {
        "name": config.host,
        "type": "A",
        "content": str(ip),
        "ttl": 60
    })


def main():
    config = parse_args()
    current_ip = get_my_ip()
    current_record, record_id = get_dns_record(config.domain, config.host, config)

    if not current_record:
        print(f"Creating {config.host}.{config.domain} with IP {current_ip}")
        create_dns_record(current_ip, config)
    elif current_ip != current_record:
        print(f"Updating {config.host}.{config.domain} from {current_record} to {current_ip}")
        update_dns_record(current_ip, record_id, config)
    else:
        print(f"Current IP {current_ip} matches DNS record {current_record}")


if __name__ == '__main__':
    main()
    exit(0)
