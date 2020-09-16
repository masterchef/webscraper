# Rent Price Scraper
A quick tool for monitoring rent prices of my apartment complex to help gauge price fluxuations.
You can see this data being visualized in [this Tableau dashboard](https://public.tableau.com/profile/viktoras.truchanovicius#!/vizhome/Prometheus/PrometheusPropertyAvailabilityandPrices?publish=yes)


# Setup
1. Create python venv ```python -m venv .venv```
2. Install dependencies ```pip install -r requirements.txt```
3. Enter venv ```source .venv/bin/activate```

# Run Options
You can run it once or on a schedule

## Single run from CLI
```
python PrometheusScrapper/scrapper.py [OPTIONS] run
```

## Scheduled run from CLI
To run it every 5 hours:
```
python PrometheusScrapper/scrapper.py [OPTIONS] schedule --hour '*/5'
```

## Scheduled run from Azure Function
You can deploy this code as Azure Function and have it run there on defined schedule in ```function.json``` file. See this [page for a how-to](https://docs.microsoft.com/en-us/azure/azure-functions/functions-develop-vs-code?tabs=csharp).

# Output Configurations
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