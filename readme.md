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

with NezamPezeshkiCrawler() as crawler:
    # Example: Get all radiologists in Mazandaran province
    doctors_data = crawler.scrape(
        province_name="مازندران", 
        specialty_name="تخصص تصویربرداری (رادیولوژی)"
    )

    # Save to pandas dataframe!
    data = pd.json_normalize(doctors_data)
    # Saving Dataset
    data.drop_duplicates(subset="Nezam").to_excel('Radiologists.xlsx', index=False)
```