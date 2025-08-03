
import re
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class NezamPezeshkiCrawler:
    """
    A web scraper to extract doctor information from membersearch.irimc.org.
    
    This class handles navigation through provinces, cities, and specialties
    to collect data about doctors based on specified criteria.
    """
    def __init__(self, parent_url: str = 'https://membersearch.irimc.org/', headless=True):
        """
        Initializes the crawler and the Selenium webdriver.
        
        Args:
            parent_url (str): Medical Council Website Address (Iran)
        """
        self.parent_url: str = parent_url
        options = None
        self.provinces_url: str = self.parent_url + 'directory'
        self.driver = webdriver.Chrome()

        # Accumulator to save all pieces of information (dictionary) for each doctor
        self.doctors_list: list = []

    def __enter__(self):
        """Allows the class to be used as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensures the webdriver is closed upon exiting the context!"""
        self.close()
    
    def close(self):
        """Closes and quits the webdriver to free up resources."""
        if self.driver:
            print("Shutting down webdriver...")
            self.driver.close()
            self.driver = None

    def _get_soup(self, url: Optional['str']=None) -> BeautifulSoup:
        """
        Fetches page content and returns a BeautifulSoup object.
        
        Args:
            url (str, optional): If provided, fetches content from this URL using requests.
                                 Otherwise, uses the current page source from the driver.

        Returns:
            BeautifulSoup: The parsed HTML content of the page.
        """
        if url:
            source = requests.get(url=url).content
        else:
            source = self.driver.page_source
        return BeautifulSoup(source, 'lxml')

    def _get_mapping(self, nth_child: int, page_link: Optional[str]=None, mode: Optional[str]=None) -> Dict[str, str]:
        """
        Gets mapping for provinces, cities, and specialties and stores them in a dictionary.

        Args:
            nth_child (int): Determines which td-child should be selected using CSS Selector.
            page_link (str): A URL to navigate to before scraping.
            mode (str): If 'specs', the function will handle pagination to find a specific specialty.
                        Otherwise, it returns the mapping from the first page.

        Returns:
            Dict[str, str]: A dictionary mapping names to URLs.
        """
        # Get the URL to navigate to
        url = self.provinces_url if page_link is None else page_link
        self.driver.get(url)

        # Get the initial mapping from the first page
        soup = self._get_soup()
        atags = soup.css.select(f"tr[role='row'] td:nth-child({nth_child}) a")
        mapping = {atag.get_text(strip=True): self.parent_url + atag.get('href') for atag in atags}

        # If not in 'specs' mode, return the mapping from the current page
        if mode is None:
            return mapping

        if self.specialty_name in mapping:
            return mapping
        
        # Get the class of the last pagination button to check its status
        last_pagination_li = soup.css.select_one('ul.pagination li:last-child')
        
        # If there's no pagination or the next button is disabled, we're done
        if not last_pagination_li or 'disabled' in last_pagination_li.get('class', []):
             return mapping
        
        # Start the pagination loop
        while True:
            # Click the next page button
            WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#DataTables_Table_0_next > a'))
            ).click()

            # Get the soup from the new page
            soup = self._get_soup()
            
            # Select new a tags and update the mapping
            atags = soup.css.select(f"tr[role='row'] td:nth-child({nth_child}) a")
            new_mapping = {atag.get_text(strip=True): self.parent_url + atag.get('href') for atag in atags}
            mapping.update(new_mapping)

            # Check if the specialty is found on the new page
            if self.specialty_name in mapping:
                return mapping

            # Check the status of the new last pagination button
            last_pagination_li = soup.css.select_one('ul.pagination li:last-child')
            if not last_pagination_li or 'disabled' in last_pagination_li.get('class', []):
                return mapping
                  
    def _parse_doctor_info(self, soup: BeautifulSoup, city_name: str)-> None:
        """Parses a page of doctor listings and appends the info to the main list."""
        trs_docs = soup.tbody.find_all('tr')
        for tr_doc in trs_docs:
            doc_cache = {}
            td_doc = tr_doc.find_all('td')

            # Cleans up doctor name which may contain extra newlines/spaces/invalid characters
            raw_doctor_name = td_doc[1].a.get_text(strip=True)
            name_parts = [part.strip() for part in re.split(r'[\r\n]+', raw_doctor_name) if part.strip()]

            try:
                WorkProvince, WorkCity = td_doc[4].a.get_text(strip=True).split('-')
            except Exception:
                WorkCity, WorkProvince = 'نامشخص', "نامشخص"
            # Saving each doctor's info in a dictionary
            doc_cache['Fullname'] = ' '.join(name_parts)
            doc_cache['Nezam'] = td_doc[2].a.get_text(strip=True)
            doc_cache['Specialty'] = td_doc[3].a.get_text(strip=True).split('|')[0]
            doc_cache['City'] = city_name
            doc_cache['AuthorizedCity'] = city_name
            doc_cache['WorkCity'] = WorkCity
            doc_cache['WorkProvince'] = WorkProvince
            doc_cache['Membership'] = td_doc[5].a.get_text(strip=True)

            # Adding each doctor's info to the global accumulator! 
            self.doctors_list.append(doc_cache)
   
    def _scrape_all_pages_for_specialty(self, spec_link: str, city_name: str):
        """Handles pagination and scrapes doctor info from all pages for a specialty."""

        # Navigate to doctors page with certain specialty
        self.driver.get(spec_link)
        initial_soup = self._get_soup()
        bowls_of_soup = []

        # Find pagination tags to obrain number of pages (for doctors with a certain specialty)
        pagination_atags = initial_soup.css.select('div.col-lg-12.col-md-12 a.btn.btn-sm.btn-round')

        if pagination_atags:
            # Obtaining common URL address for all pages...
            main_pagination_elements = pagination_atags[0].get('href').split('/')[:-1]
            main_pagination_url = '/'.join(main_pagination_elements) + '/'

            # Extract the total number of pages from the last pagination button
            num_pages = int(re.findall(r'\d+', str(pagination_atags[-1].string))[0])
            # Get soup from all pages
            for page_number in range(1, num_pages + 1):
                page_url = self.parent_url + main_pagination_url + str(page_number)
                soup = self._get_soup(url=page_url)
                bowls_of_soup.append(soup)
        else:
            # if pagination atags is empty, it means that we only have one page to scrape!
            bowls_of_soup.append(initial_soup)

        for soup in bowls_of_soup:
            self._parse_doctor_info(soup, city_name)

    def scrape(self, province_name: str, specialty_name: str)-> List[Dict]:
        """
        
        Main funtion of the class. it triggers the scraping job!

        """
        self.specialty_name = specialty_name

        # Process Begins...
        print(f"🔍 Starting scrape for province '{province_name}' and specialty '{specialty_name}'...")
        
        province_mapping = self._get_mapping(nth_child=3)
        province_link = province_mapping.get(province_name)

        cities_mapping = self._get_mapping(page_link=province_link, nth_child=2)
        for city_name, city_link in cities_mapping.items():

            print(f"✅  Processing city: {city_name}")

            # Searching withing each city and scrape all of the doctors
            spec_mapping = self._get_mapping(page_link=city_link, nth_child=2, mode='specs')
            spec_link = spec_mapping.get(specialty_name)
            # Check whether or not the city has the specific specialty
            if spec_link:
                self._scrape_all_pages_for_specialty(spec_link, city_name)
            else:
                print(f"❌  Specialty not found in {city_name}.")
        
        # Process Ends...
        print(f"\n✅ Scraping complete. Found {len(self.doctors_list)} doctors.")
        return self.doctors_list.copy()


if __name__ == '__main__':
    import pandas as pd

    with NezamPezeshkiCrawler() as crawler:
        # Example: Get all radiologists in Mazandaran province
        doctors_data = crawler.scrape(
            province_name="مازندران", 
            specialty_name="تخصص تصویربرداری (رادیولوژی)"
        )

        # Save to pandas dataframe!
        data = pd.json_normalize(doctors_data)
        # Saving Dataset
        data.drop_duplicates(subset="Nezam").to_excel('DoctorsList.xlsx', index=False)