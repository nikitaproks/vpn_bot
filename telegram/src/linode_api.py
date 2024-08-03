import os
import json
import logging
from typing import Any
from enum import Enum

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Region(Enum):
    DALLAS = "us-central"
    SINGAPORE = "ap-south"
    FRANKFURT = "eu-central"
    LONDON = "eu-west"
    AMSTERDAM = "nl-ams"
    MILAN = "it-mil"
    PARIS = "fr-par"
    MADRID = "es-mad"


class StackscriptData(BaseModel):
    ...


class ShadowsocksStackscriptData(StackscriptData):
    SERVER_PORT: int = 8388
    LOCAL_PORT: int = 1080
    TIMEOUT: int = 600
    METHOD: str = "chacha20-ietf-poly1305"
    PASSWORD: str


class Linode(BaseModel):
    id: int
    label: str
    region: str
    ipv4: list[str]

    def __str__(self) -> str:
        msg = ""
        msg += f"ID:        {self.id}\n"
        msg += f"Label:     {self.label}\n"
        msg += f"Region:    {self.region}\n"
        msg += f"IP:        {', '.join(self.ipv4)}"
        return msg


class LinodeAPI:
    def __init__(self, api_key: str) -> None:
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        self.client = httpx.Client()
        self.base_url = "https://api.linode.com/v4"

    def _send_request(
        self,
        method: str,
        path: str,
        params: list[tuple[str, Any]] | None = None,
        data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        return self.client.request(
            method,
            self.base_url + path,
            headers=self.headers,
            json=data,
            params=params,
        )

    def create_linode(
        self,
        region: str,
        image: str = "linode/ubuntu20.04",
        type: str = "g6-nanode-1",
        label: str | None = None,
        stackscript_id: int | None = None,
        stackscript_data: StackscriptData | None = None,
    ):
        data = {
            "type": type,
            "image": image,
            "region": region,
            "label": label,
            "root_pass": os.urandom(16).hex(),
            "stackscript_id": stackscript_id,
            "stackscript_data": stackscript_data.model_dump()
            if stackscript_data
            else None,
        }
        return self._send_request("POST", "/linode/instances", data=data)

    def list_linodes(
        self,
        page: int,
        page_size: int = 100,
    ):
        params = [("page", page), ("page_size", page_size)]
        return self._send_request("GET", "/linode/instances", params=params)

    def list_linodes_all(self) -> list[Linode]:
        page = 1
        linodes = []
        while True:
            response = self.list_linodes(page)
            data = response.json()["data"]
            if not (data := response.json()["data"]):
                break
            linodes.extend(data)
            page += 1
        return [Linode(**linode) for linode in linodes]

    def delete_linode(self, linode_id: int) -> bool:
        response = self._send_request("DELETE", f"/linode/instances/{linode_id}")
        return response.status_code == httpx.codes.OK
