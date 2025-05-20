#%%
import asyncio
import datetime
import pandas as pd
from playwright.async_api import async_playwright

async def scraper(browser):
    page = await browser.new_page()
    
    #Access the market URL
    await page.goto('https://www.samsclub.com.br/', wait_until="load")

    #Getting away from the cookies modal
    await page.get_by_role("button", name="Proceed with all").click()

    #Selecting the region of the market
    await page.get_by_role("button", name="Informar CEP").click()
    await page.get_by_placeholder("Digite aqui o CEP").fill("14405289")

    btn = page.locator("#button")
    await btn.click()
    await btn.wait_for(state='hidden')

    #Scrolling the page
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

    #Click on slide buttons to get all product impressions
    slide_btn = await page.get_by_role("button", name="Next Slide").all()
    slide_btn = slide_btn[1:]

    for button in slide_btn:
        for i in range(5):
            await button.click()

    #Processing DataLayer
    data_layer = await page.evaluate("window.dataLayer")    

    items_dl = [event['ecommerce']['items'] for event in data_layer if event.get('event') =="view_item_list"]
    items = [item for sublista in items_dl for item in sublista]

    #Generating the final DF
    df = pd.DataFrame(items)
    df['date'] = datetime.date.today().strftime('%Y-%m-%d')
    df['market'] = 'SAMS CLUB'
    
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