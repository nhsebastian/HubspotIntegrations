from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from urllib.parse import urlencode
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from os import getenv
from pprint import pprint
from hubspot import HubSpot
from hubspot.crm.contacts import BatchInputSimplePublicObjectId, ApiException
import httpx
import uvicorn
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")
load_dotenv()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hubspot")
async def hubspot(req: Request):
    return templates.TemplateResponse(name = "index.html", context={"request": req})

@app.get("/login")
def get_hubspot_oauth_url():
    params = {
        "client_id": getenv('CLIENT_ID'),
        "redirect_uri": getenv('REDIRECT_URI'),
        "scope": "oauth crm.objects.contacts.read",
        "response_type": "code"
    }
    return RedirectResponse(f"https://app.hubspot.com/oauth/authorize?{urlencode(params)}")


@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(request: Request, code: str):
    try:
        print(f"Received authorization code: {code}")
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": getenv('CLIENT_ID'),
                    "client_secret": getenv('CLIENT_SECRET'),
                    "redirect_uri": getenv('REDIRECT_URI'),
                    "code": code
                }
            )

            print(f"Token response status: {token_response.status_code}")
            print(f"Token response body: {token_response.text}")

            if token_response.status_code == 200:
                tokens = token_response.json()
                return templates.TemplateResponse(
                    "success.html",
                    {"request": request, "tokens": tokens}
                )
            else:
                error_detail = token_response.json().get("error_description", "Unknown error")
                return templates.TemplateResponse(
                    "error.html",
                    {"request": request, "error": error_detail}
                )
    except Exception as e:
        print(f"Error during token exchange: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)}
        )

@app.get("/refresh_token")
def refresh_hubspot_token(request: Request, refresh_token: str):
    try:
        url = "https://api.hubapi.com/oauth/v1/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": getenv('CLIENT_ID'),
            "client_secret": getenv('CLIENT_SECRET'),
            "refresh_token": refresh_token
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        token_response = requests.post(url, data=data, headers=headers)
        token_response.raise_for_status()
        print(f"Token response status: {token_response.status_code}")
        print(f"Token response body: {token_response.text}")

        if token_response.status_code == 200:
            tokens = token_response.json()
            return templates.TemplateResponse(
                "success.html",
                {"request": request, "tokens": tokens}
            )
        else:
            error_detail = token_response.json().get("error_description", "Unknown error")
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": error_detail}
            )
    except Exception as e:
        print(f"Error during token exchange: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)}
        )

@app.get("/getcontacts", response_class=HTMLResponse)
async def get_contacts(request: Request, access_key: str):
    try:
        print(f"Access Key Received: {access_key}")

        api_client = HubSpot(access_token=access_key)
        contacts = api_client.crm.contacts.get_all()
        #########
        # url = "https://api.hubapi.com/contacts/v1/lists/all/contacts/all"
        # data = {
        #     "access_token": access_key,
        #     "grant_type": "refresh_token",
        #     "client_id": getenv('CLIENT_ID'),
        #     "client_secret": getenv('CLIENT_SECRET'),
        # }
        # headers ={
        #     "Content-Type": "application/json",
        # }
        # api_repsponse = requests.post(url, data=data, headers=headers)
        # print(api_repsponse)

        return templates.TemplateResponse(
            "contacts.html", {"request": request, "contacts": contacts}
        )
    except Exception as e:
        print(f"Error during contacts retrieval: {str(e)}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )
if __name__ == "__main__":
    uvicorn.run("main:app")
