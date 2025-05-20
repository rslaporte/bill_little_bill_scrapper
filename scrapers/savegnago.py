#%%
import asyncio
import datetime
import pandas as pd
from playwright.async_api import async_playwright

async def scraper(browser):
    page = await browser.new_page()
    
    #Access the market URL
    await page.goto('https://www.savegnago.com.br/', wait_until="load")

    #Getting away from the cookies modal
    await page.get_by_role("button", name="Allow all cookies").click()  

    #Selecting the region of the market
    region_btn = (await page.locator(".regionalizationStoreButton").all())[0]
    await region_btn.click()
    
    await page.get_by_role("button", name="Retirar na loja").click()
    await page.get_by_placeholder("Pesquise por cidade").fill("Franca - Jardim Integracao")
    await page.get_by_text("Franca - Jardim Integracao", exact=True).click()
    await page.get_by_role("button", name="Ir as compras").click()

    #Getting to the promotion page
    await page.get_by_text("Ofertas do Folheto", exact=True).click()

    #Getting all the product impressions
    await page.evaluate("""
        async () => {
            window.scrollBy(0,50)                
        }    
    """)

    for i in range(5):
        await page.get_by_label("Next Slide").click()

    #Scrolling the page to the end
    await page.evaluate("""
        async () => {
            let totalHeight = 0;
            const distance = 100;

            while (totalHeight < document.body.scrollHeight) {
                window.scrollBy(0, distance);
                totalHeight += distance;
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }
    """)

    await asyncio.sleep(5)
    #Processing DataLayer
    data_layer = await page.evaluate("window.dataLayer")    

    items_dl = [event['ecommerce']['items'] for event in data_layer if event.get('event') =="view_item_list"]
    items = [item for sublista in items_dl for item in sublista]

    #Generating the final DF
    df = pd.DataFrame(items)
    df['date'] = datetime.date.today().strftime('%Y-%m-%d')
    df['market'] = 'SAVEGNAGO'
    
    #Saving DF
    df[['date',
        'market', 
        'item_name', 
        'item_category', 
        'item_brand', 
        'price']].to_csv('./test.csv', index=False)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Upgrade-Insecure-Requests": "1",
                "DNT": "1",  # Do Not Track
            }
        )
    
        await scraper(context)
        await browser.close()

asyncio.run(main())