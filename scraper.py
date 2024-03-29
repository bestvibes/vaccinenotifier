#!/usr/bin/env python3

import sys
import datetime
import time
import os
import random

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from twilio.rest import Client
from fake_useragent import UserAgent
from twilio.base.exceptions import TwilioRestException

class Params:
    SPREADSHEET_NUM_COLS = 10
    SPREADSHEET_SUB_INDEX = 1
    SPREADSHEET_CONSENT_INDEX = 2
    SPREADSHEET_AGE_INDEX = 3
    SPREADSHEET_INDUSTRY_INDEX = 4
    SPREADSHEET_COUNTY_INDEX = 5
    SPREADSHEET_UNDCONDITION_INDEX = 6
    SPREADSHEET_DISABILITY_INDEX = 7
    SPREADSHEET_ZIPCODE_INDEX = 8
    SPREADSHEET_PHONE_INDEX = 9

    SCRAPER_NUM_ARGS = 4 # no sub/unsub or timestamp
    SCRAPER_AGE_INDEX = 0
    SCRAPER_COUNTY_INDEX = 1
    SCRAPER_ZIPCODE_INDEX = 2
    SCRAPER_PHONE_INDEX = 3

    SPREADSHEET_TO_SCRAPER_MAP = {
        SPREADSHEET_AGE_INDEX : SCRAPER_AGE_INDEX,
        SPREADSHEET_COUNTY_INDEX : SCRAPER_COUNTY_INDEX,
        SPREADSHEET_ZIPCODE_INDEX : SCRAPER_ZIPCODE_INDEX,
        SPREADSHEET_PHONE_INDEX : SCRAPER_PHONE_INDEX
    }

SLEEPTIME = 3
CHROMEDRIVER = os.environ['CHROMEDRIVER_PATH']

def get_age_ranges():
    return ["16 - 17", "18 and older"]
def get_industries():
    return ["Chemical and hazardous materials", "Communications and IT", "Critical manufacturing", "Defense",
            "Education and childcare", "Emergency services", "Energy", "Financial services",
            "Food and Agriculture", "Government operations / community based essential functions", "Healthcare Worker",
            "Industrial, commercial, residential, and sheltering facilities and services",
            "Retired", "Transportation and logistics", "Unemployed", "Water and wastewater",
            "Other"]
def age_to_range(age):
    age_ranges = get_age_ranges()
    if isinstance(age, str) and age in age_ranges:
        ret = age
    else:
        age = int(age)
        if age <= 17:
            ret = age_ranges[0]
        else:
            ret = age_ranges[1]
    assert ret in age_ranges, ret
    return ret

def get_element(driverwait, xpath):
    return driverwait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

def get_elements(driverwait, xpath):
    return driverwait.until(EC.presence_of_all_elements_located(((By.XPATH, xpath))))

def main():
    if len(sys.argv) != Params.SCRAPER_NUM_ARGS+1:
        print(sys.argv)
        print(f"Usage: {sys.argv[0]} age county zipcodes recipientgroups")
        sys.exit(1)

    sys.argv = list(map(lambda x: x.replace('"', ""), sys.argv))
    currtime = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    age = sys.argv[Params.SCRAPER_AGE_INDEX+1]
    county = sys.argv[Params.SCRAPER_COUNTY_INDEX+1]
    zipcodes = sys.argv[Params.SCRAPER_ZIPCODE_INDEX+1].split('|')
    recipientgroups = sys.argv[Params.SCRAPER_PHONE_INDEX+1].split('||')

    recipientgroups = list(map(lambda x: x.split("|"), recipientgroups))

    assert county[0].isupper(), county
    assert len(zipcodes)==len(recipientgroups)
    assert all(map(lambda z: len(z) == 5, zipcodes))
    for recipientgroup in recipientgroups:
        for recipient in recipientgroup:
            assert(recipient[0] == '+' and recipient[1] == '1' and len(recipient)==12)

    age = age_to_range(age)

    try:
        print(f"Checking for age={age} county={county} zip={zipcodes} at {currtime}\nrecipients={recipientgroups}")
        URL = 'https://myturn.ca.gov'
        options = webdriver.ChromeOptions()
        if 'HEAD' not in os.environ:
            options.add_argument('headless')
        # user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
        user_agent = ""
        while len(user_agent) == 0 or "MSIE 10.0; Windows 3.1" in user_agent:
            ua = UserAgent()
            agents = [ua.ie, ua.safari]
            user_agent = agents[random.randint(0, len(agents)-1)]
        print("user-agent:", user_agent)
        options.add_argument(f'user-agent={user_agent}')
        driver = webdriver.Chrome(CHROMEDRIVER, options=options)
        driver.implicitly_wait(SLEEPTIME) # seconds
        driver.get(URL)
        wait = WebDriverWait(driver, 10)

        if len(driver.find_elements_by_xpath("//div[@role='alert' and contains(text(), 'making important changes to the website')]")) > 0:
            print("SITE UNDER MAINTENANCE")
            return

        get_element(wait, "//button[@type='button' and @data-testid='landing-page-continue']").click()
        get_element(wait, "//input[@name='q-screening-18-yr-of-age']").click()
        get_element(wait, "//input[@name='q-screening-health-data']").click()
        get_element(wait, "//input[@name='q-screening-privacy-statement']").click()
        get_element(wait, "//input[@name='q-screening-eligibility-age-range' and @value='{}']".format(age)).click()
        get_element(wait, "//select[@name='q-screening-eligibility-county']/option[text()='{}']".format(county)).click()
        get_element(wait, "//input[@name='q-screening-different-county' and @value='{}']".format("No")).click()
        get_element(wait, "//button[@type='submit']").click()

        wait.until(EC.url_matches("(ineligible|location)"))

        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        fromnumber = os.environ['TWILIO_FROM_NUMBER']
        maintainernum = os.environ['MAINTAINER_NUM']
        signuplink = os.environ['SIGNUP_LINK']
        tclient = Client(account_sid, auth_token)
        if 'ineligible' in driver.current_url:
            print(f"INELIGIBLE for age={age} county={county}")
        elif 'location' in driver.current_url:
            print(f"ELIGIBLE for age={age} county={county}")

            for zipcode, recipientgroup in zip(zipcodes, recipientgroups):
                print(f"CHECKING APPTS for zipcode={zipcode} recipients={recipientgroup}")
                zipcode_input = get_element(wait, "//input[@id='location-search-input']")
                zipcode_input.send_keys(Keys.BACKSPACE * 5);
                zipcode_input.send_keys(zipcode+Keys.RETURN)
                WebDriverWait(driver, 2).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))

                if 'No appointments are available' in driver.page_source:
                    print(f"APPOINTMENTS NOT AVAILABLE for zipcode={zipcode} recipients={recipientgroup}!")
                elif 'Unable to find a location' in driver.page_source:
                    print(f"INVALID LOCATION for zipcode={zipcode} recipients={recipientgroup}!")
                    continue
                else:
                    apptfound = False
                    numlocations = len(driver.find_elements_by_xpath("//button[@type='button' and contains(text(),'See availability')]"))
                    for i in range(numlocations):
                        all_locations = get_elements(wait, "//button[@type='button' and contains(text(),'See availability')]")
                        if (len(all_locations) > i):
                            location = all_locations[i]
                        else:
                            continue
                        location.click()
                        for _ in range(2): # up to 1 months ahead
                            WebDriverWait(driver, 2).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))
                            available_dates = driver.find_elements_by_xpath("//td[@role='button' and @aria-disabled='false']")
                            for date in available_dates:
                                WebDriverWait(driver, 2).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))
                                date.click()
                                WebDriverWait(driver, 2).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))
                                # hasappts = get_elements(wait, "//button[@type='button' and @data-testid='appointment-select-timeslot']")
                                try:
                                    hasappts = get_elements(wait, "//*[@type='button' and (contains(text(), 'am') or contains(text(), 'pm') or contains(text(), 'AM') or contains(text(), 'PM'))]")
                                except TimeoutException:
                                    hasappts = []
                                if len(hasappts) > 0:
                                    apptfound = True
                                    break
                            if not apptfound:
                                WebDriverWait(driver, 2).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))
                                get_element(wait, "//button[@type='button' and @class='calendar__next']").click()
                            else:
                                break
                        WebDriverWait(driver, 4).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))
                        get_element(wait, "//a[@data-testid='appointment-select-change-location']").click()
                        if apptfound:
                            break
                    if apptfound:
                        print(f"APPOINTMENTS AVAILABLE for zipcode={zipcode} recipients={recipientgroup}!")
                        for recipient in recipientgroup:
                            try:
                                message = tclient.messages.create(
                                    body=f"Appointments available for {age} at {county},{zipcode}. Current time is {currtime}. {URL}. If you already have an appointment, you can unsubscribe at {signuplink}.",
                                    from_=fromnumber,
                                    to=recipient
                                )
                                print(recipient, message.sid)
                            except TwilioRestException as e:
                                if "blacklist rule" in str(e):
                                    print(recipient, "BLACKLIST:", e)
                                else:
                                    print("stre:", str(e))
                                    raise e
                    else:
                        print(f"CALENDAR BUT APPOINTMENTS NOT AVAILABLE for zipcode={zipcode} recipients={recipientgroup}!")
                # go back
                if zipcode != zipcodes[-1]:
                    WebDriverWait(driver, 2).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))
                    get_element(wait, "//a[contains(text(),'Change')]").click()
        else:
            print("IDK WHERE I AM:", driver.current_url)
            message = tclient.messages.create(
                body=f"Notifier failed for {age} at {county},{zipcodes} at {currtime}!",
                from_=fromnumber,
                to=maintainernum
            )
            print(maintainernum, message.sid)
    except TimeoutException as e:
        if (driver):
            print(driver.current_url)
            print(driver.page_source)
        raise e
    finally:
        driver.close()

if __name__ == "__main__":
    main()
