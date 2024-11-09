import base64
import time
from datetime import datetime, timezone
from typing import Optional, Union

from betterproto import Casing, Message
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from requests import JSONDecodeError, Response

from .errors import SettradeError

LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo


def create_sha256_with_ecdsa_signature(secret: str, content: str):
    decode = base64.b64decode(secret)
    private_key = ec.derive_private_key(int.from_bytes(decode, "big"), ec.SECP256R1())
    signature = private_key.sign(content.encode(), ec.ECDSA(hashes.SHA256()))
    return signature.hex()


def get_current_milli_timestamp_str() -> str:
    return str(int(time.time() * 1000))


def get_current_datetime() -> datetime:
    return datetime.now().astimezone(LOCAL_TIMEZONE)


def get_current_timestamp() -> int:
    return int(time.time())


def truncate_timestamp(target_time: int, duration: int) -> int:
    return target_time // duration * duration


def response_to_dict(res: Response):
    if not res.ok:
        data = res.json()
        raise SettradeError(
            code=data["code"],
            status_code=res.status_code,
            message=data["message"],
        )
    try:
        data = res.json()
    except JSONDecodeError:
        # case cancel/change order
        return {}
    return data


def mqtt_to_message(is_success: bool, data: Union[str, dict]):
    # SUCCESS CASE ...
    if is_success:
        return {"is_success": True, "data": data}

    # ERROR CASE ...
    try:
        if isinstance(data, str):
            return {"is_success": False, "message": data}

        if "rejectSubscriptions" in data:
            return {
                "is_success": False,
                "message": data["rejectSubscriptions"][0]["errorMessage"],
            }

        return {"is_success": False, "data": data}
    except:
        return {"is_success": False, "data": data}


def money_to_dict(self, *_, **__) -> float:
    return self.units + self.nanos / 1e9
