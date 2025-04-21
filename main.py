from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from urllib.parse import urlencode
from fastapi.responses import HTMLResponse
from fastapi import HTTPException
from dotenv import load_dotenv
from os import getenv
import httpx
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")
load_dotenv()


def get_hubspot_oauth_url():
    params = {
        "client_id": getenv('CLIENT_ID'),
        "redirect_uri": getenv('REDIRECT_URI'),
        "scope": "contacts",
        "response_type": "code"
    }
    return f"https://app.hubspot.com/oauth/authorize?{urlencode(params)}"

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hubspot")
async def hubspot(req: Request):
    return templates.TemplateResponse(name = "index.html", context={"request": req})

@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(code: str):
    """
    Handle the OAuth callback from HubSpot.
    This endpoint will receive the authorization code that can be exchanged for access tokens.
    """
    try:
        print(f"Received authorization code: {code}")
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": getenv('CLIENT_ID'),
                    "client_secret": getenv('CLIENT_SECRET'),
                    "redirect_uri": getenv('REDIRECT_URI') ,
                    "code": code
                }
            )

            print(f"Token response status: {token_response.status_code}")
            print(f"Token response body: {token_response.text}")

            if token_response.status_code == 200:
                tokens = token_response.json()
                return HTMLResponse("success.html", 200, {'tokens': tokens})
            else:
                error_detail = token_response.json().get("error_description", "Unknown error")
                return HTMLResponse(error.html, 400, {'error': error_detail})
    except Exception as e:
        print(f"Error during token exchange: {str(e)}")
        return HTMLResponse(content=create_error_html(str(e)))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    uvicorn.run("main:app")
