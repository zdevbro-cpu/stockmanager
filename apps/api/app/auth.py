"""Firebase Auth JWT 검증(스텁).

Production에서는 아래 중 하나로 구현하세요.
1) Google public keys(JWKS)로 서명 검증 + aud/iss/project_id 확인
2) firebase-admin SDK를 백엔드에서 사용하여 verify_id_token

여기서는 '구조만' 제공하고, 실제 검증 로직은 TODO로 남깁니다.
"""

from fastapi import Depends, HTTPException, Header


def get_current_user(authorization: str | None = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization scheme")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")

    # TODO: Verify JWT and extract claims
    # Return a lightweight user dict for now
    return {"uid": "local-dev", "token_present": True}
