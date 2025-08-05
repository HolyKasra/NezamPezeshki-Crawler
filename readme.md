# Medical Council Website `Crawler`

A web scraper to extract doctor information from the Iranian Medical Council website.

## 💡 General Concept 
- This project scrapes doctor information (name, specialty, registration number, etc.) from [Medical Council Website](`membersearch.irimc.org`). 
- It systematically navigates through provinces → cities → specialties to collect comprehensive data.


## 🛠️ Main Algorithm 
The crawler uses a hierarchical scraping approach:
- Maps all available provinces
- For each province, maps all cities
- For each city, maps all medical specialties
- For each specialty, scrapes all paginated results
- Parses and stores doctor information in a structured format using `CSS Selector` method

## 📋 Requirements

This project has below dependencies

- `pandas`  dealing with dataframes
- `bs4` Beautiful Soup for web scraping and parsing htmls
- `selenium` for the website automation
- `requests` for HTTP requests to websites
- `re` regular expression library

## 💡 Example Usage 
```python
import pandas as pd
from pyscraper import NezamPezeshkiCrawler
all_radiologists = []

with NezamPezeshkiCrawler() as crawler:

    provinces_mappings = crawler._get_mapping(nth_child=3)
    # Example: Get all radiologists in Mazandaran province

    for province in provinces_mappings.keys():
        doctors_data = crawler.scrape(
            province_name=province, 
            specialty_name="تخصص تصویربرداری (رادیولوژی)"
        )

        # Saving Doctors From All Provinces
        all_radiologists.extend([*doctors_data])

# Saving doctors data to a dataframe
df = pd.json_normalize(all_radiologists)
# Exporting Data as an excel file
df.drop_duplicates(subset="Nezam").to_excel('Radiologists.xlsx', index=False)
```