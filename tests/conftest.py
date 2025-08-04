from fastapi import Depends, HTTPException


def fake_auth(dep_check: bool = Depends(lambda: True)):
    if not dep_check:
        raise HTTPException(status_code=403, detail="Unauthorized")
