#!/usr/bin/env python3

import sys
import datetime
import time
import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from twilio.rest import Client

class Params:
    SPREADSHEET_NUM_COLS = 10
    SPREADSHEET_SUB_INDEX = 1
    SPREADSHEET_CONSENT_INDEX = 2
    SPREADSHEET_PHONE_INDEX = SPREADSHEET_NUM_COLS-1

    SCRAPER_NUM_ARGS = 7 # no sub/unsub or timestamp
    SCRAPER_AGE_INDEX = 0
    SCRAPER_INDUSTRY_INDEX = 1
    SCRAPER_COUNTY_INDEX = 2
    SCRAPER_ZIPCODE_INDEX = 3
    SCRAPER_UNDCONDITION_INDEX = 4
    SCRAPER_DISABILITY_INDEX = 5
    SCRAPER_PHONE_INDEX = 6

SLEEPTIME = 3
CHROMEDRIVER = '/Users/vaibhavaggarwal/projects/vaccinenotifier/chromedriver'

def get_age_ranges():
    return ["16 - 49", "50-64", "65 - 74", "75 and older"]
def get_industries():
    return ["Chemical and hazardous materials", "Communications and IT", "Critical manufacturing", "Defense",
            "Education and childcare", "Emergency services", "Energy", "Financial services",
            "Food and Agriculture", "Government operations / community based essential functions", "Healthcare Worker",
            # "Industrial, commercial, residential, and sheltering facilities and services",
            "Retired", "Transportation and logistics", "Unemployed", "Water and wastewater",
            "Other"]
def age_to_range(age):
    age_ranges = get_age_ranges()
    if isinstance(age, str) and age in age_ranges:
        ret = age
    else:
        age = int(age)
        if age <= 49:
            ret = age_ranges[0]
        elif age <= 64:
            ret = age_ranges[1]
        elif age <= 74:
            ret = age_ranges[2]
        else:
            ret = age_ranges[3]
    assert ret in age_ranges, ret
    return ret

def get_element(driverwait, xpath):
    return driverwait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

def get_elements(driverwait, xpath):
    return driverwait.until(EC.presence_of_all_elements_located(((By.XPATH, xpath))))

def main():
    if len(sys.argv) != Params.SCRAPER_NUM_ARGS+1:
        print(sys.argv)
        print(f"Usage: {sys.argv[0]} age industry county zipcode undcond recipient")
        sys.exit(1)

    currtime = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    age = sys.argv[Params.SCRAPER_AGE_INDEX+1]
    industry = sys.argv[Params.SCRAPER_INDUSTRY_INDEX+1]
    county = sys.argv[Params.SCRAPER_COUNTY_INDEX+1]
    zipcode = sys.argv[Params.SCRAPER_ZIPCODE_INDEX+1]
    undcondition = sys.argv[Params.SCRAPER_UNDCONDITION_INDEX+1]
    disability = sys.argv[Params.SCRAPER_DISABILITY_INDEX+1]
    recipients = sys.argv[Params.SCRAPER_PHONE_INDEX+1].split('|')

    assert industry in get_industries(), industry
    assert county[0].isupper(), county
    assert len(zipcode) == 5
    assert undcondition in ["Yes", "No"]
    for recipient in recipients:
        assert(recipient[0] == '+' and recipient[1] == '1' and len(recipient)==12)

    age = age_to_range(age)

    try:
        print(f"Checking for age={age} ind={industry} county={county} zip={zipcode} und={undcondition} dis={disability} at {currtime}\nrecipients={recipients}")
        URL = 'https://myturn.ca.gov'
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(SLEEPTIME) # seconds
        driver.get(URL)
        wait = WebDriverWait(driver, 10)

        get_element(wait, "//button[@type='button' and @data-testid='landing-page-continue']").click()
        get_element(wait, "//input[@name='q-screening-18-yr-of-age']").click()
        get_element(wait, "//input[@name='q-screening-health-data']").click()
        get_element(wait, "//input[@name='q-screening-privacy-statement']").click()
        get_element(wait, "//input[@name='q-screening-eligibility-age-range' and @value='{}']".format(age)).click()
        get_element(wait, "//input[@name='q-screening-underlying-health-condition' and @value='{}']".format(undcondition)).click()
        get_element(wait, "//input[@name='q-screening-disability' and @value='{}']".format(disability)).click()
        get_element(wait, "//select[@name='q-screening-eligibility-industry']/option[text()='{}']".format(industry)).click()
        get_element(wait, "//select[@name='q-screening-eligibility-county']/option[text()='{}']".format(county)).click()
        get_element(wait, "//button[@type='submit']").click()

        wait.until(EC.url_matches("(ineligible|location)"))

        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        fromnumber = os.environ['TWILIO_FROM_NUMBER']
        maintainernum = os.environ['MAINTAINER_NUM']
        signuplink = os.environ['SIGNUP_LINK']
        tclient = Client(account_sid, auth_token)
        if 'ineligible' in driver.current_url:
            print(f"INELIGIBLE for age={age} county={county} industry={industry} und={undcondition} dis={disability}")
        elif 'location' in driver.current_url:
            print(f"ELIGIBLE for age={age} county={county} industry={industry} und={undcondition} dis={disability}")

            get_element(wait, "//input[@id='location-search-input']").send_keys(zipcode+Keys.RETURN)
            WebDriverWait(driver, 2).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))

            if 'No appointments are available' in driver.page_source:
                print("APPOINTMENTS NOT AVAILABLE!")
                # for recipient in recipients:
                # message = tclient.messages.create(
                # body=f"Appointments not available for {age} in {industry} at {zipcode} at {currtime}. {URL}. Unsubscribe at {signuplink}.",
                # from_=fromnumber,
                # to=recipient
                # )
                # print(recipient, message.sid)
            else:
                apptfound = False
                numlocations = len(driver.find_elements_by_xpath("//button[@type='button' and contains(text(),'See availability')]"))
                for i in range(numlocations):
                    location = get_elements(wait, "//button[@type='button' and contains(text(),'See availability')]")[i]
                    location.click()
                    for _ in range(2): # up to 1 months ahead
                        WebDriverWait(driver, 2).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))
                        available_dates = driver.find_elements_by_xpath("//td[@role='button' and @aria-disabled='false']")
                        for date in available_dates:
                            WebDriverWait(driver, 2).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))
                            date.click()
                            WebDriverWait(driver, 2).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))
                            hasappts = get_elements(wait, "//*[contains(text(), 'appointments available')]")
                            if len(hasappts) > 0 and not hasappts[0].text.startswith("0 appointments"):
                                apptfound = True
                                break
                        if not apptfound:
                            WebDriverWait(driver, 2).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))
                            get_element(wait, "//button[@type='button' and @class='calendar__next']").click()
                        else:
                            break
                    if not apptfound:
                        WebDriverWait(driver, 4).until(EC.invisibility_of_element((By.XPATH, "//div[class='loader-background']")))
                        get_element(wait, "//a[@data-testid='appointment-select-change-location']").click()
                    else:
                        break

                if apptfound:
                    print("APPOINTMENTS AVAILABLE!")
                    for recipient in recipients:
                        message = tclient.messages.create(
                            body=f"Appointments available for {age} in {industry} at {county},{zipcode}. Current time is {currtime}. {URL}. If you already have an appointment, you can unsubscribe at {signuplink}.",
                            from_=fromnumber,
                            to=recipient
                        )
                        print(recipient, message.sid)
                else:
                    print("APPOINTMENTS NOT AVAILABLE!")
        else:
            print("IDK WHERE I AM:", driver.current_url)
            message = tclient.messages.create(
                body=f"Notifier failed for {age} in {industry} at {county},{zipcode} und={undcondition} dis={disability} at {currtime}!",
                from_=fromnumber,
                to=maintainernum
            )
            print(maintainernum, message.sid)
    except TimeoutException as e:
        if (driver):
            print(driver.page_source)
        raise e
    finally:
        driver.close()

if __name__ == "__main__":
    main()
