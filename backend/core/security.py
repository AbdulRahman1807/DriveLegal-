import os
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

security = HTTPBearer()

# For a production system this should validate a real JWT from Firebase/Auth0/etc.
# For now, we will use a static MASTER_API_KEY to protect the endpoint from public scraping.
MASTER_API_KEY = os.environ.get("MASTER_API_KEY", "drivelegal-secret-dev-key")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
    if credentials.credentials != MASTER_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key or JWT token.")
    return credentials.credentials
