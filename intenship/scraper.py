from datetime import datetime
import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager


def get_movie_count():
    while True:
        try:
            count = int(input("Enter number of IMDb movies to scrape (1-250): "))

            if 1 <= count <= 250:
                return count
            else:
                print("Please enter a number between 1 and 250.")

        except ValueError:
            print("Invalid input. Enter only numbers.")


movie_count = get_movie_count()

options = Options()

# Comment this line if you want to see the browser
options.add_argument("--headless=new")

options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")

options.add_argument(
    "--disable-blink-features=AutomationControlled"
)

options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

print("\nStarting Chrome Browser...\n")

service = Service(ChromeDriverManager().install())

driver = webdriver.Chrome(
    service=service,
    options=options
)

wait = WebDriverWait(driver, 20)

print("Browser Started Successfully")

url = "https://www.imdb.com/chart/top/"

driver.get(url)

print(f"\nOpening IMDb Page:\n{url}")

time.sleep(5)

movies = []

try:

    movie_items = wait.until(
        EC.presence_of_all_elements_located(
            (
                By.CSS_SELECTOR,
                "li.ipc-metadata-list-summary-item"
            )
        )
    )

except:

    movie_items = driver.find_elements(
        By.XPATH,
        "//li[contains(@class,'ipc-metadata-list-summary-item')]"
    )

print(f"\nFound {len(movie_items)} Movies")
print(f"Collecting Top {movie_count} Movies...\n")

for index, item in enumerate(movie_items[:movie_count], start=1):

    try:

        title = "N/A"
        year = "N/A"
        duration = "N/A"
        rating = "N/A"
        movie_url = ""

        try:
            link = item.find_element(
                By.CSS_SELECTOR,
                "a.ipc-title-link-wrapper"
            )

            title = link.text.strip()
            movie_url = link.get_attribute("href")

        except:
            pass

        try:
            metadata = item.find_elements(
                By.CSS_SELECTOR,
                "span.cli-title-metadata-item"
            )

            if len(metadata) >= 1:
                year = metadata[0].text

            if len(metadata) >= 2:
                duration = metadata[1].text

        except:
            pass

        try:
            rating = item.find_element(
                By.CSS_SELECTOR,
                "span.ipc-rating-star--rating"
            ).text

        except:
            pass

        movies.append(
            {
                "Rank": index,
                "Title": title,
                "Year": year,
                "Duration": duration,
                "Rating": rating,
                "Country": "N/A",
                "MovieURL": movie_url,
            }
        )

        print(
            f"{index:>3} | "
            f"{rating} | "
            f"{year} | "
            f"{duration} | "
            f"{title}"
        )

    except Exception as e:

        print(f"Error in Movie {index}: {e}")

print("\nCollecting Country Information...\n")

for movie in movies:

    try:

        if movie["MovieURL"] == "":
            continue

        driver.get(movie["MovieURL"])

        wait.until(
            EC.presence_of_element_located(
                (By.TAG_NAME, "body")
            )
        )

        time.sleep(2)

        country_links = driver.find_elements(
            By.XPATH,
            "//a[contains(@href,'country_of_origin')]"
        )

        countries = []

        for country in country_links:

            text = country.text.strip()

            if text:
                countries.append(text)

        if countries:
            movie["Country"] = ", ".join(countries)

        print(
            f"{movie['Rank']:>3} | "
            f"{movie['Country']} | "
            f"{movie['Title']}"
        )

    except Exception as e:

        print(
            f"Country Not Found for Rank "
            f"{movie['Rank']} : {e}"
        )

driver.quit()

print("\nBrowser Closed Successfully")

if len(movies) == 0:

    print("\nNo movie data collected.")
    exit()

df = pd.DataFrame(movies)

columns_required = [
    "Rank",
    "Title",
    "Year",
    "Duration",
    "Rating",
    "Country"
]

df = df[columns_required]

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

file_name = f"imdb_top_movies_{timestamp}.csv"

df.to_csv(file_name, index=False)

print("\nCSV File Saved Successfully:")
print(file_name)

print("\nTop Movies Preview:\n")

print(df.head(10).to_string(index=False))

print("\nScraping Completed Successfully!")