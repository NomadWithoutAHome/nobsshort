from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from deta import Deta
from pydantic import BaseModel
import validators
from typing import Optional
import time
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

# Initialize FastAPI app
app = FastAPI()

# Initialize Deta Base
deta = Deta('b0Acb3MNMF6j_TWrzYi2yRtVas7TMtwwgGLLDg4gP8G6P')  # replace 'project_key' with your actual project key
db = deta.Base('urls')

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

class Url(BaseModel):
    long_url: str
    custom_key: Optional[str] = None

def is_valid_url(url):
    if validators.url(url):
        return True
    return False

@app.get("/sitemap.xml")
async def get_sitemap_xml():
    sitemap_patch = "static/sitemap.xml"
    return FileResponse(sitemap_patch, media_type="text/xml")

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post('/shorten/')
async def create_url(url: Url):
    url_data = url.dict()
    long_url = url_data['long_url']
    custom_key = url_data.get('custom_key')

    if custom_key and db.get(custom_key):
        raise HTTPException(status_code=400, detail="Custom key already exists")

    if not long_url.startswith(('http://', 'https://')):
        long_url = 'http://' + long_url
    if not is_valid_url(long_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    if not custom_key:
        # Generate a unique key if no custom key is provided
        new_url = db.put({'long_url': long_url}, expire_in=int(time.time()) + 7 * 24 * 3600)
    else:
        new_url = db.put({'long_url': long_url}, key=custom_key)

    short_url = f"http://shorturl.nobss.online/{new_url['key']}"
    return {'id': new_url['key'], 'short_url': short_url, 'long_url': long_url}
@app.get('/{id}')
async def get_url(id: str):
    url_data = db.get(id)
    if url_data is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return RedirectResponse(url=url_data['long_url'])
