from dataclasses import dataclass
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


BASE_URL = "https://quotes.toscrape.com/"


def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def parse_quotes_from_page(soup: BeautifulSoup) -> list[Quote]:
    quotes_data = []
    quote_elements = soup.find_all("div", class_="quote")
    for quote in quote_elements:
        text = quote.find("span", class_="text").get_text()
        author = quote.find("small", class_="author").get_text()
        tags = [tag.get_text() for tag in quote.find_all("a", class_="tag")]
        quotes_data.append(Quote(text, author, tags))
    return quotes_data


def get_author_bio(author_url: str) -> str:
    soup = get_soup(author_url)
    bio_div = soup.find("div", class_="author-description")
    return bio_div.get_text(strip=True) if bio_div else ""


def scrape_all_quotes() -> list[Quote]:
    quotes = []
    authors_cache = {}
    page_url = BASE_URL
    while page_url:
        print(f"Scraping page: {page_url}")
        soup = get_soup(page_url)
        page_quotes = parse_quotes_from_page(soup)

        for quote in page_quotes:
            quotes.append(quote)
            author = quote.author
            if author not in authors_cache:
                author_page_relative = soup.find(
                    "a",
                    href=True,
                    text=author
                )["href"]

                author_page_url = urljoin(BASE_URL, author_page_relative)
                bio = get_author_bio(author_page_url)
                authors_cache[author] = bio

        next_button = soup.find("li", class_="next")
        if next_button:
            next_relative = next_button.find("a")["href"]
            page_url = urljoin(BASE_URL, next_relative)
        else:
            page_url = None

    return quotes, authors_cache


def write_quotes_to_csv(quotes: list[Quote], output_csv_path: str) -> None:
    fieldnames = ["text", "author", "tags"]
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for quote in quotes:
            writer.writerow({
                "text": quote.text,
                "author": quote.author,
                "tags": ",".join(quote.tags)
            })


def write_authors_to_csv(authors: dict, output_csv_path: str) -> None:
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
