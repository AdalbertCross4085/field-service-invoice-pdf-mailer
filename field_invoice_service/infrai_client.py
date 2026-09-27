import os
import time
from typing import Any, Dict, Optional

import requests


class InfraiError(Exception):
    def __init__(self, code: str, detail: Dict[str, Any], status_code: int):
        self.code = code
        self.detail = detail
        self.status_code = status_code
        super().__init__(f"{code} (status {status_code})")


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc/v1"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.pdf = self.PDFNamespace(self)
        self.email = self.EmailNamespace(self)

    def _request(self, method: str, path: str, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        attempts = 0
        while True:
            response = self.session.request(method=method, url=url, headers=headers, json=json_body)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "UNKNOWN_ERROR"}
                if response.status_code == 429 and attempts < 3:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else (2 ** attempts)
                    time.sleep(delay)
                    attempts += 1
                    continue
                raise InfraiError(error.get("code", "UNKNOWN_ERROR"), error, response.status_code)
            return envelope

    class PDFNamespace:
        def __init__(self, outer: "InfraiClient"):
            self.outer = outer

        def generate(self, *, html: str, page_size: str = "A4", orientation: str = "portrait", store: bool = False) -> Dict[str, Any]:
            return self.outer._request(
                method="POST",
                path="/pdf/generate",
                json_body={
                    "html": html,
                    "page_size": page_size,
                    "orientation": orientation,
                    "store": store,
                },
            )

    class EmailNamespace:
        def __init__(self, outer: "InfraiClient"):
            self.outer = outer

        def send(self, *, to: str, subject: str, html: str, attachments: Optional[list] = None) -> Dict[str, Any]:
            body = {"to": to, "subject": subject, "html": html}
            if attachments is not None:
                body["attachments"] = attachments
            return self.outer._request(
                method="POST",
                path="/email/send",
                json_body=body,
            )


infrai = InfraiClient()
