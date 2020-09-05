# Rent Price Scraper
A quick tool for monitoring rent prices of my apartment complex to help gauge price fluxuations.

## Setup
1. Create python venv ```python -m venv```
2. Install dependencies ```pip install -r requirements.txt```

## Configure Output
By default the script will output to console but you can enable email sending and logging to google sheets.

### Email Support
Pass ```--email``` flag to the script, provide your google account username as ```--username``` argument and enter password when prompted:
```
python scrapper.py --email --username username@gmail.com --email_to to_email@gmail.com
```

### GSheets Support
1. Create a Google API project and setup a service account. https://console.developers.google.com/apis/credentials
2. Download the API credentials and store it at the root of the project as ```credentials.json```
3. Create a google sheet to store the results.
4. Share the sheet with your service account user, eg ```scrapper@scrapersheet.iam.gserviceaccount.com```
5. Pass ```--gsheet``` flag to the script and your document key as ```--doc-key``` argument.


## Run Options
You can run it once or on a schedule

### Once
```
python scrapper.py [OPTIONS] run
```

### Schedule
To run it every 5 hours:
```
python scrapper.py [OPTIONS] schedule --hour '*/5'
```
