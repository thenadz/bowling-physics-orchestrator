#!/usr/bin/env python3

import argparse
import json
import random
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, NoReturn, Type
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Make "app.*" importable when run as a script.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas.auth import Token
from app.schemas.bowling_config import CreateSimulationReq
from app.schemas.responses import CreateOrGetSimulationResp


def model_validate(model_cls: Type[Any], payload: Dict[str, Any]) -> Any:
    return model_cls.model_validate(payload)


def model_dump(model: Any) -> Dict[str, Any]:
    return model.model_dump()


def _raise_connection_error(method: str, url: str, err: URLError) -> NoReturn:
    reason = getattr(err, "reason", err)
    raise RuntimeError(
        f"{method} {url} -> connection failed: {reason}. "
        "Check --base-url and ensure API is running "
        "(example: http://127.0.0.1:8888)."
    ) from err


def http_json(
    method: str,
    url: str,
    *,
    body: Dict[str, Any] | None = None,
    headers: Dict[str, str] | None = None,
    expected_status: int | None = None,
) -> Dict[str, Any]:
    req_headers = {"Accept": "application/json", **(headers or {})}
    data = None
    if body is not None:
        req_headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    req = Request(url=url, method=method, data=data, headers=req_headers)
    try:
        with urlopen(req) as resp:
            raw = resp.read().decode("utf-8").strip()
            if expected_status is not None and resp.status != expected_status:
                raise RuntimeError(
                    f"{method} {url} -> {resp.status}, expected {expected_status}"
                )
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> {e.code}: {detail}") from e
    except URLError as e:
        _raise_connection_error(method, url, e)


def http_form(
    method: str,
    url: str,
    *,
    form: Dict[str, str],
    expected_status: int | None = None,
) -> Dict[str, Any]:
    req = Request(
        url=url,
        method=method,
        data=urlencode(form).encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req) as resp:
            raw = resp.read().decode("utf-8").strip()
            if expected_status is not None and resp.status != expected_status:
                raise RuntimeError(
                    f"{method} {url} -> {resp.status}, expected {expected_status}"
                )
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> {e.code}: {detail}") from e
    except URLError as e:
        _raise_connection_error(method, url, e)


def random_create_sim_req() -> CreateSimulationReq:
    return CreateSimulationReq(
        velocity=round(random.uniform(7.5, 9.0), 2),
        rpm=random.randint(200, 400),
        friction=round(random.uniform(0.035, 0.055), 3),
        angle=round(random.uniform(0.0, 3.0), 2),
        lateral_offset=round(random.uniform(-0.1, 0.1), 3),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Create user, fetch token, then send create-simulation requests."
    )
    parser.add_argument("--base-url", default="http://localhost:8888", help="Base URL of the API (running within IDE devcontainer requires host.docker.internal)")
    parser.add_argument("--count", type=int, default=5, help="1..500")
    parser.add_argument("--pause-ms", type=int, default=200, help="Pause between requests")
    parser.add_argument("--password", required=True, help="Password for the seeded user")
    parser.add_argument("--stop-on-error", action="store_true")

    if len(sys.argv) == 1:
        parser.print_help()
        return 2

    args = parser.parse_args()

    if args.count < 1 or args.count > 500:
        raise SystemExit("--count must be between 1 and 500")
    if args.pause_ms < 0:
        raise SystemExit("--pause-ms must be >= 0")

    base = args.base_url.rstrip("/")
    username = f"seed_{uuid.uuid4().hex[:12]}"

    # /users expects query params in current contract
    create_user_url = f"{base}/users?{urlencode({'username': username, 'password': args.password})}"
    http_json("POST", create_user_url, expected_status=201)
    print(f"created user={username}")

    token_payload = http_form(
        "POST",
        f"{base}/token",
        form={"username": username, "password": args.password},
        expected_status=200,
    )
    token = model_validate(Token, token_payload)
    auth_headers = {"Authorization": f"Bearer {token.access_token}"}

    ok = 0
    failed = 0
    for i in range(args.count):
        req_model = random_create_sim_req()
        try:
            payload = model_dump(req_model)
            resp = http_json(
                "POST",
                f"{base}/simulations",
                body=payload,
                headers=auth_headers,
                expected_status=202,
            )
            model_validate(CreateOrGetSimulationResp, resp)
            ok += 1
            print(f"[{i + 1}/{args.count}] created")
        except Exception as ex:
            failed += 1
            print(f"[{i + 1}/{args.count}] failed: {ex}", file=sys.stderr)
            if args.stop_on_error:
                raise

        if i < args.count - 1 and args.pause_ms > 0:
            time.sleep(args.pause_ms / 1000.0)

    print(f"done success={ok} failed={failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())