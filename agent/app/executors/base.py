from typing import Any, Dict


def make_result(success: bool, message: str, **extra: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {"success": success, "message": message}
    if extra:
        result.update(extra)
    return result
