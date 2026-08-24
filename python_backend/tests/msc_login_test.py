from DrissionPage import ChromiumOptions, ChromiumPage
import time

def msc_test():
    print("Starting MSC Headless Test...")
    co = ChromiumOptions()
    co.set_argument('--headless=new')
    page = ChromiumPage(co)
    
    login_url = "https://mscciam.b2clogin.com/mscciam.onmicrosoft.com/oauth2/v2.0/authorize?p=b2c_1a_signupsignin&client_id=a67f5969-b5a5-4de0-ae50-f611dfa91fee&redirect_uri=https%3A%2F%2Fidentityserver.msc.com%2Fsignin-aad-b2c&response_type=id_token&scope=openid%20profile&response_mode=form_post&nonce=639222171119370305.ZjQ5MzgwMjUtNmU0ZS00YTBhLTlkMzUtOGUxNWNmOWIyOTY5NDIxYTU4ZTctMWNmMi00MDFjLWJkMTYtNWIzMWEyM2ZhMTcx&ui_locales=en&state=CfDJ8JCi0WqCtPVEprDHFnXVEfN_34jKWVGyEMTLZoEdP2pfKeiMVJ_-rmOwAYp_QO-riwpog7AW7yvjCmZSJLXBlc9fp49cU6mhv4omHBAHFSjHSTHlAgTq5FLTS7_UttKGCU5crkbrCQGu3EV8oOeVHOgFyNPncQS01xxyIlkBq3RE&x-client-SKU=ID_NET9_0&x-client-ver=8.0.1.0"
    
    print("Navigating to login URL...")
    page.get(login_url)
    time.sleep(5)
    
    print("Looking for email field...")
    email_field = page.ele('@type=email') or page.ele('@name=logonIdentifier') or page.ele('#logonIdentifier')
    if email_field:
        email_field.input('alejandro.delcarpio@primeteam.com.mx')
        print("Entered email.")
    
    print("Looking for password field...")
    pass_field = page.ele('@type=password') or page.ele('@name=password') or page.ele('#password')
    if pass_field:
        pass_field.input('Adc19770123$')
        print("Entered password.")
        
    next_btn = page.ele('@id=next') or page.ele('text:Sign in') or page.ele('@type=submit')
    if next_btn:
        next_btn.click()
        print("Clicked sign in.")
        
    time.sleep(10)
    print("Current URL:", page.url)
    
    print("Page HTML:")
    print(page.html[:1000])
    
    page.quit()

if __name__ == '__main__':
    msc_test()
