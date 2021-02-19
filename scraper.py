#!/usr/bin/env python3

import sys
import datetime
import time
import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from twilio.rest import Client

FROMNUMBER="+15102161731"
SLEEPTIME = 3
CHROMEDRIVER = '/Users/vaibhavaggarwal/projects/vaccinenotifier/chromedriver'

def get_age_ranges():
    return ["Under 16", "16 - 49", "50-64", "65 - 74", "75 and older"]
def get_industries():
    return ["Financial services", "Education and childcare", "Communications and IT", "65 - 74", "75 and older"]
def age_to_range(age):
    age_ranges = get_age_ranges()
    if isinstance(age, str) and age in age_ranges:
        ret = age
    else:
        age = int(age)
        if age <= 16:
            ret = age_ranges[0]
        elif age <= 49:
            ret = age_ranges[1]
        elif age <= 64:
            ret = age_ranges[2]
        elif age <= 74:
            ret = age_ranges[3]
        else:
            ret = age_ranges[4]
    assert ret in age_ranges, ret
    return ret

def main():
    if len(sys.argv) != 5:
        print(sys.argv)
        print(f"Usage: {sys.argv[0]} age industry zipcode recipient")
        sys.exit(1)

    currtime = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    age = sys.argv[1]
    industry = sys.argv[2]
    zipcode = sys.argv[3]
    recipients = sys.argv[4].split(',')

    assert len(zipcode) == 5
    for recipient in recipients:
        assert(recipient[0] == '+' and recipient[1] == '1' and len(recipient)==12)

    age = age_to_range(age)

    print(f"Checking for age={age} ind={industry} recipients={recipients} zip={zipcode} at {currtime}")
    URL = 'https://myturn.ca.gov'
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(CHROMEDRIVER, options=options)
    driver.get(URL)

    time.sleep(SLEEPTIME)
    # driver.find_element_by_xpath("//button[@data-testid='landing-page-continue']").click()
    driver.find_element_by_xpath('//*[@id="root"]/div/main/div[1]/div/div[2]/div[2]/button').click()
    time.sleep(SLEEPTIME)
    driver.find_element_by_xpath("//input[@name='q-screening-18-yr-of-age']").click()
    driver.find_element_by_xpath("//input[@name='q-screening-health-data']").click()
    driver.find_element_by_xpath("//input[@name='q-screening-privacy-statement']").click()
    driver.find_element_by_xpath("//input[@name='q-screening-eligibility-age-range' and @value='{}']".format(age)).click()
    driver.find_element_by_xpath("//select[@name='q-screening-eligibility-industry']/option[text()='{}']".format(industry)).click()
    driver.find_element_by_xpath("//select[@name='q-screening-eligibility-county']/option[text()='Alameda']").click()
    driver.find_element_by_xpath("//button[@type='submit']").click()
    time.sleep(SLEEPTIME)

    if 'ineligible' in driver.current_url:
        print(f"INELIGIBLE for age={age} and industry={industry}")
    elif 'location' in driver.current_url:
        print(f"ELIGIBLE for age={age} and industry={industry}")

        driver.find_element_by_xpath("//input[@id='location-search-input']").send_keys(zipcode+Keys.RETURN)
        # driver.find_element_by_xpath("//*[@id='root']/div/main/div/div[3]/button[1]").click()
        time.sleep(SLEEPTIME)

        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        tclient = Client(account_sid, auth_token)
        if 'No appointments are available' in driver.page_source:
            print("APPOINTMENTS NOT AVAILABLE!")
            # for recipient in recipients:
            # message = tclient.messages.create(
            # body=f"Appointments not available for {age} in {industry} at {zipcode} at {currtime}. {URL}",
            # from_=FROMNUMBER,
            # to=recipient
            # )
            # print(recipient, message.sid)
        else:
            print("APPOINTMENTS AVAILABLE!")
            for recipient in recipients:
                message = tclient.messages.create(
                    body=f"Appointments available for {age} in {industry} at {zipcode} at {currtime}. {URL}",
                    from_=FROMNUMBER,
                    to=recipient
                )
                print(recipient, message.sid)
    else:
        print("IDK WHERE I AM:", driver.current_url)

    driver.close()

if __name__ == "__main__":
    main()
