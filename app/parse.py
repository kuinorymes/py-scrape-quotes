from dataclasses import dataclass
import csv
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]



BASE_URL = "https://quotes.toscrape.com/"

def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def parse_quotes_from_page(soup):
    quotes_data = []
    quote_elements = soup.find_all("div", class_="quote")
    for quote in quote_elements:
        text = quote.find("span", class_="text").get_text()
        author = quote.find("small", class_="author").get_text()
        tags = [tag.get_text() for tag in quote.find_all("a", class_="tag")]
        author_page_relative = quote.find("a")["href"]
        author_page_url = urljoin(BASE_URL, author_page_relative)
        quotes_data.append({
            "text": text,
            "author": author,
            "tags": str(tags),
            "author_url": author_page_url
        })
    return quotes_data

def get_author_bio(author_url):
    soup = get_soup(author_url)
    bio_div = soup.find("div", class_="author-description")
    return bio_div.get_text(strip=True) if bio_div else ""

def scrape_all_quotes():
    quotes = []
    authors_cache = {}
    page_url = BASE_URL

    while page_url:
        print(f"Scraping page: {page_url}")
        soup = get_soup(page_url)
        page_quotes = parse_quotes_from_page(soup)

        for quote in page_quotes:
            quotes.append(quote)
            author = quote["author"]

            if author not in authors_cache:
                bio = get_author_bio(quote["author_url"])
                authors_cache[author] = bio

        next_button = soup.find("li", class_="next")

        if next_button:
            next_relative = next_button.find("a")["href"]
            page_url = urljoin(BASE_URL, next_relative)

        else:
            page_url = None
    return quotes, authors_cache

def write_quotes_to_csv(quotes, output_csv_path):
    fieldnames = ["text", "author", "tags"]
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for quote in quotes:
            writer.writerow({
                "text": quote["text"],
                "author": quote["author"],
                "tags": quote["tags"]
            })

def write_authors_to_csv(authors, output_csv_path):
    authors_csv_path = output_csv_path.rsplit(".", 1)[0] + "_authors.csv"
    fieldnames = ["author", "biography"]
    with open(authors_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for author, bio in authors.items():
            writer.writerow({
                "author": author,
                "biography": bio
            })

def main(output_csv_path: str) -> None:
    quotes, authors = scrape_all_quotes()
    write_quotes_to_csv(quotes, output_csv_path)
    write_authors_to_csv(authors, output_csv_path)


if __name__ == "__main__":
    main("quotes.csv")
