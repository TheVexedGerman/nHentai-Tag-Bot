import json
from aiohttp import web
from aiohttp import ClientSession
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from postgres_credentials import DISCORD_HOOK_URL

from DBConn import Database
database = Database()
options = ChromeOptions()
options.headless = False
driver = uc.Chrome(options=options, version_main=119)

async def handle(request):
    galleryNumber = request.match_info.get('galleryNumber', "Anonymous")
    database.execute("SELECT last_update, json FROM nhentai WHERE (gallery_number = %s)", [galleryNumber])
    cachedEntry = database.fetchone()
    if cachedEntry:
        return web.json_response(cachedEntry[1])
    driver.get(f'https://nhentai.net/api/gallery/{galleryNumber}')
    try:
        WebDriverWait(driver, timeout=30).until(EC.presence_of_element_located((By.XPATH, '//meta[@name="color-scheme"]')))
    except:
        error = 408
        async with ClientSession() as session:
            response = await session.get(url=DISCORD_HOOK_URL,
                                        data='{"username": "nHentai-Relay", "content": f"Failed fetching gallery"}',
                                        headers={"Content-Type": "application/json"})
            print(await response.json())
        return web.Response(text="408 Error", status=error)
    element = driver.find_element(By.XPATH, "//pre")
    nhentaiTags = json.loads(element.text)
    return web.json_response(nhentaiTags)

app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/{galleryNumber}', handle)])

if __name__ == '__main__':
    web.run_app(app)