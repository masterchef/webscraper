import datetime
import gspread
import getpass
import pandas as pd
import re
import smtplib
import time
import click

from email.message import EmailMessage

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from apscheduler.schedulers.background import BlockingScheduler
from oauth2client.service_account import ServiceAccountCredentials

DOC_KEY = '1XZocxmyQ91e1exBvwDAaSR8Rhavy9WPnwLSz0Z5SKsM'

@click.group()
@click.option('--email', is_flag=True, help='A flag for sending email with results.')
@click.option('--email_to', help='CSV of email addresses to send notification to.')
@click.option('--username', help='SMTP account username.')
@click.option('--gsheet', is_flag=True, help='A flag for updating google sheet with results')
@click.option('--doc_key', help='Google Doc Key to update')
@click.pass_context
def cli(ctx, email, email_to, username, gsheet, doc_key):
    ctx.ensure_object(dict)        
    if email and (not username or not email_to):
        print('Please provide email sending parameters')
        exit(0)
    elif email:
        password = getpass.getpass("Please enter your google account password for sending email:\n")
        ctx.obj['password'] = password
    if gsheet and not doc_key:
        print('Please provide a gsheet doc key')
        exit(0)
    pass


@cli.command('schedule')
@click.option('--hour', default='*/1', help='Cron hour expression')
@click.pass_context
def schedule(ctx, hour):
    email = ctx.parent.params['email']
    username = ctx.parent.params['username']
    email_to = ctx.parent.params['email_to']
    password = ctx.obj.get('password', None)
    gsheet = ctx.parent.params['gsheet']
    doc_key = ctx.parent.params['doc_key']

    schedule = BlockingScheduler()
    schedule.add_job(run, kwargs={"email": email, "gsheet": gsheet, "doc_key": doc_key, "username": username, "email_to": email_to, "password": password}, trigger='cron', hour=hour)
    try:
        schedule.start()
    except (KeyboardInterrupt, SystemExit):
        schedule.shutdown()


@cli.command('run')
@click.pass_context
def once(ctx):
    email = ctx.parent.params['email']
    gsheet = ctx.parent.params['gsheet']
    username = ctx.parent.params['username']
    email_to = ctx.parent.params['email_to']
    password = ctx.obj.get('password', None)
    doc_key = ctx.parent.params['doc_key']
    run(email, username, email_to, password, gsheet, doc_key)


def run(email, username, email_to, password, gsheet, doc_key):
    content = {}
    content.update(get_prometheus_apartments('https://prometheusapartments.com/search/?term=San+Francisco+Bay+Area'))
    content.update(get_prometheus_apartments('https://prometheusapartments.com/search/?term=Portland'))
    content.update(get_prometheus_apartments('https://prometheusapartments.com/wa/gig-harbor-apartments/cliffside/'))

    formatted_content = format_email(content)
    if email:
        send_email(username, password, email_to, [content for content in formatted_content if  'mansion-grove' in content.keys()])
    
    if gsheet:
        update_historical_data(doc_key, content)
    print(formatted_content)


def get_prometheus_apartments(url):
    content = {}
    driver = get_browser()
    driver.get(url)
    try:
        anchors = driver.find_elements_by_xpath("//div[@id='results-cards']/div/a[@class='card-wrapper']")
    except Exception as e:
        print(f'{e}')
        return content

    links = [a.get_attribute('href') for a in anchors]
    apartments = []
    for apt in links:
        name = apt.strip('/').split('/')[-1]
        apartments.append({'name': name, 'url': f'{apt}lease'})
    for apt in apartments:
        content[apt['name']] = get_availability(apt['url'])
    return content


def update_historical_data(doc_key, content):
    date = datetime.datetime.today().strftime('%Y-%m-%d')
    all_content = []
    for key, data in content.items():
        for row in data:
            cleaned_values = [f'{date}', f'{key}'] + [value.replace('$', '').replace(',', '') for value in row]
            all_content.append(cleaned_values)
    update_gdoc(doc_key, all_content)


def format_email(content):
    result = ''
    for key, data in content.items():
        result += f'------------ {key} ----------------\n'
        total_available = sum(int(row[-1]) for row in data)
        result += '\n'.join(', '.join(row) for row in data)
        result += f'\nTotal Available: {total_available}\n'
    
    result += f'For historical data click the link below:\nhttps://docs.google.com/spreadsheets/d/1XZocxmyQ91e1exBvwDAaSR8Rhavy9WPnwLSz0Z5SKsM/edit?usp=sharing'
    return result


def get_browser():
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1200")

    DRIVER_PATH = './chromedriver'
    return webdriver.Chrome(options=options, executable_path=DRIVER_PATH)

 
def get_availability(url):
    driver = get_browser()
    driver.get(url)
    content = []
    print(f'Processing {url}')
    delay = 30 # seconds
    try:
        WebDriverWait(driver, delay).until(EC.frame_to_be_available_and_switch_to_it('rp-leasing-widget'))
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'primary')][contains(text(), 'Start')]")))
    except TimeoutException:
        print('Waiting for iframe')

    # import pdb; pdb.set_trace()
    try:
        driver.find_element_by_xpath("//button[contains(@class, 'primary')][contains(text(), 'Start')]").click()
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'ng-binding')]")))
        driver.find_element_by_xpath("//a[contains(@class, 'ng-binding')]").click()


        # Print plan prices
        names = driver.find_elements_by_xpath("//div[contains(@class, 'floorplan-tile')]/div/span[contains(@class, 'name')]")
        specs = driver.find_elements_by_xpath("//div[contains(@class, 'floorplan-tile')]/div/span[contains(@class, 'specs')]")
        prices = driver.find_elements_by_xpath("//div[contains(@class, 'floorplan-tile')]/div/span[contains(@class, 'range')]")
        availability = driver.find_elements_by_xpath("//div[contains(@class, 'floorplan-tile')]/div[@class='tile-buttons']/button")
    except Exception as e:
        print(f'{e}')
        print(f'Unable to parse {url}')
        return content

    for i in range(len(names)):
        match = re.match(r'\((\d+)\).*', availability[i].text)
        units = 0
        if match:
            units = int(match.groups()[0])
        min_price = prices[i].text.split(' - ')[0] if prices[i].text.strip()  else '0'
        content.append((names[i].text, specs[i].text, min_price, str(units)))
    driver.quit()
    return content


def send_email(username, password, to, content):
    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = f'Apartment availability'
    msg['From'] = username
    msg['To'] = to

    # Send the message via our own SMTP server.
    s = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    s.login(username, password)
    s.send_message(msg)
    s.quit()


def update_gdoc(doc_key, cells):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", scope,
    )

    docs = gspread.authorize(credentials)
    sheet = docs.open_by_key(doc_key).sheet1
    new = pd.DataFrame(cells)
    new.columns = ['Date', 'Complex', 'Plan', 'Specs', 'Price', 'Availability']
    existing = pd.DataFrame(sheet.get_all_values()[1:])
    if existing.size:
        existing.columns = ['Date', 'Complex', 'Plan', 'Specs', 'Price', 'Availability']
    updated = existing.append(new)
    updated = updated.groupby(['Date', 'Complex', 'Plan', 'Specs']).min()
    updated.reset_index(inplace=True)
    sheet.update([updated.columns.values.tolist()] + updated.values.tolist(), value_input_option='USER_ENTERED')


if __name__ == '__main__':
    cli()
