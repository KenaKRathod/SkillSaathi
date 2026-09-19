import csv
import sys
from bs4 import BeautifulSoup
import requests
from pathlib import Path

def parse_row(row_html):
    """Parse a single course card HTML into a dictionary of fields."""
    name = row_html.find('h3', class_='course-title')
    scheme = row_html.find('span', class_='scheme-name')
    sector = row_html.find('span', class_='sector-name')
    nsqf = row_html.find('span', class_='nsqf-level')
    duration = row_html.find('span', class_='duration')
    cost = row_html.find('span', class_='cost')
    
    return {
        'name': name.text.strip() if name else '',
        'scheme': scheme.text.strip() if scheme else 'PMKVY 4.0',
        'sector': sector.text.strip() if sector else '',
        'nsqf_level': nsqf.text.strip() if nsqf else '',
        'duration': duration.text.strip() if duration else '',
        'cost': cost.text.strip() if cost else '',
        'district_availability': '',
        'min_age': '',
        'max_age': '',
        'min_education': '',
        'wage_outcome': '',
        'source_url': 'https://www.skillindiadigital.gov.in/sector/list?forCourse=true',
        'data_confidence': 'scraped'
    }

def scrape_programs():
    url = "https://www.skillindiadigital.gov.in/sector/list?forCourse=true"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('div', class_='course-card')
    except Exception as e:
        print(f"Failed to fetch: {e}")
        rows = []
    
    programs = [parse_row(r) for r in rows]
    return programs

def main():
    programs = scrape_programs()
    
    if len(programs) < 10:
        with open("manual_entry_needed.md", "w", encoding="utf-8") as f:
            f.write("# Manual Entry Needed\n\n")
            f.write("The scraper returned fewer than 10 rows. Fields missing:\n")
            f.write("- Structural changes, SPA blocking, or no items found.\n")
        print("Scraping failed or returned < 10 rows. Wrote manual_entry_needed.md")
        return
        
    for p in programs:
        # Check if fields are missing to set 'partial' confidence
        # 'name', 'scheme', 'sector', 'nsqf_level', 'duration', 'cost', 'district_availability', 'min_age', 'max_age', 'min_education', 'wage_outcome'
        if not p.get('duration') or not p.get('cost') or not p.get('nsqf_level'):
            p['data_confidence'] = 'partial'
            p['source_url'] += ' | https://www.msde.gov.in/static/uploads/2024/02/PMKVY-4.0-Guidelines_final-copy.pdf'
            
    Path("data").mkdir(exist_ok=True)
    with open("data/skilling_programs.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            'name', 'scheme', 'sector', 'nsqf_level', 'duration', 'cost',
            'district_availability', 'min_age', 'max_age', 'min_education',
            'wage_outcome', 'source_url', 'data_confidence'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(programs)
    print(f"Successfully scraped {len(programs)} programs to data/skilling_programs.csv")

if __name__ == "__main__":
    main()
