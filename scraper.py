"""
Product Sentiment Analyzer - Web Scraper Module

This module handles web scraping from Amazon and Flipkart using Selenium.
It focuses on extracting meaningful review data even when the target websites
change their markup or add extra UI elements.
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from config import Config

logger = logging.getLogger(__name__)


# ============================================================================
# AMAZON SCRAPER
# ============================================================================


def scrape_amazon(product_name: str, min_reviews: int = 50) -> List[Dict[str, Any]]:
    """Scrape product reviews from Amazon India in the same order the user requested."""
    logger.info(f"Starting Amazon scraper for: {product_name}")

    driver = None
    reviews: List[Dict[str, Any]] = []

    try:
        driver = _create_chrome_driver()

        logger.info("Opening Amazon India...")
        driver.get("https://www.amazon.in/?language=en_IN")
        time.sleep(3)

        logger.info(f"Searching for product: {product_name}")
        search_summary = _amazon_search_product(driver, product_name)
        if not search_summary.get("opened"):
            logger.warning("No suitable Amazon product could be opened")
            return []

        logger.info(f"Search result count detected: {search_summary.get('result_count')}")
        logger.info(f"Selected Amazon product: {search_summary.get('selected_title')}")
        time.sleep(3)

        logger.info("Opening the product review section...")
        review_summary = _amazon_open_reviews_page(driver)
        if review_summary.get("opened"):
            logger.info(f"Review section opened successfully. Review count detected: {review_summary.get('review_count')}")
        else:
            logger.warning("The Amazon review section could not be opened")
        time.sleep(3)

        logger.info(f"Scraping reviews (minimum: {min_reviews})...")
        reviews = _amazon_scrape_reviews(driver, min_reviews, product_name)
        logger.info(f"✓ Scraped {len(reviews)} reviews from Amazon")

    except TimeoutException as exc:
        logger.error(f"Timeout while scraping Amazon: {exc}")
    except WebDriverException as exc:
        logger.error(f"WebDriver error: {exc}")
    except Exception as exc:
        logger.error(f"Error scraping Amazon: {exc}", exc_info=True)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    return reviews


def _amazon_search_product(driver, product_name: str) -> Dict[str, Any]:
    """Search Amazon and open the matching product result while reporting the result count."""
    search_selectors = [(By.ID, "twotabsearchtextbox"), (By.NAME, "field-keywords")]

    try:
        search_box = None
        for by, value in search_selectors:
            try:
                search_box = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((by, value)))
                break
            except TimeoutException:
                continue

        if search_box is None:
            raise TimeoutException("Amazon search box not found")

        search_box.clear()
        time.sleep(0.5)
        search_box.send_keys(product_name)
        time.sleep(0.5)
        search_box.submit()

        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result'], div.s-result-item"))
        )

        result_count = _extract_search_result_count(driver)
        logger.info(f"Amazon search results page loaded. Result count: {result_count}")

        for _ in range(6):
            products = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result'], div.s-result-item")
            if not products:
                time.sleep(2)
                continue

            for product in products:
                try:
                    if "sponsored" in (product.text or "").lower():
                        continue

                    product_text = (product.text or "").strip()
                    candidate_links = product.find_elements(By.TAG_NAME, "a")
                    for link in candidate_links:
                        href = link.get_attribute("href") or ""
                        if not href or "slredirect" in href or "/dp/" not in href and "/gp/product/" not in href:
                            continue

                        title = product_text if product_text else (link.text or "")
                        if title and not _looks_like_product_match(title, product_name) and len(products) > 1:
                            continue

                        logger.info("Opening Amazon product page")
                        driver.get(href)
                        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                        time.sleep(3)
                        return {"opened": True, "result_count": result_count, "selected_title": title}
                except Exception as exc:
                    logger.debug(f"Amazon product candidate failed: {exc}")
                    continue

            time.sleep(2)

        logger.warning("No suitable Amazon product result was opened")
        return {"opened": False, "result_count": result_count, "selected_title": ""}

    except TimeoutException as exc:
        logger.error(f"Amazon search results did not load: {exc}")
        return {"opened": False, "result_count": None, "selected_title": ""}
    except Exception as exc:
        logger.error(f"Search failed: {exc}")
        return {"opened": False, "result_count": None, "selected_title": ""}


def _amazon_open_reviews_page(driver) -> Dict[str, Any]:
    """Use the product page review count when Amazon blocks the review URL and avoid unnecessary redirects."""
    try:
        fallback_review_count = _extract_amazon_review_count(driver)
        if fallback_review_count:
            logger.info(f"Amazon product page already exposes {fallback_review_count} reviews; using that value")
            return {"opened": False, "review_count": fallback_review_count}

        for _ in range(6):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(1.2)

            selectors = [
                "a[data-hook='see-all-reviews-link-foot']",
                "a[href*='product-reviews']",
                "a[href*='customerReviews']",
                "#reviews-medley-footer a",
                "a.a-link-emphasis",
                "#customer-reviews_feature_div a",
            ]

            for selector in selectors:
                try:
                    links = driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in links:
                        if not link.is_displayed():
                            continue
                        href = link.get_attribute("href") or ""
                        if not href:
                            continue
                        logger.info("Opening Amazon reviews page")
                        driver.get(href)
                        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                        time.sleep(3)
                        if _is_amazon_access_blocked(driver):
                            logger.warning("Amazon review page is protected, returning the product-page review count")
                            return {"opened": False, "review_count": fallback_review_count}
                        review_count = _extract_amazon_review_count(driver) or fallback_review_count
                        return {"opened": True, "review_count": review_count}
                except Exception:
                    continue

            asin = _extract_amazon_asin(driver.current_url)
            if asin:
                direct_review_url = f"https://www.amazon.in/product-reviews/{asin}/ref=cm_cr_getr_d_paging_btm_next_1"
                logger.info("Opening Amazon review URL directly")
                driver.get(direct_review_url)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(3)
                if _is_amazon_access_blocked(driver):
                    logger.warning("Amazon review page is protected, returning the product-page review count")
                    return {"opened": False, "review_count": fallback_review_count}
                review_count = _extract_amazon_review_count(driver) or fallback_review_count
                return {"opened": True, "review_count": review_count}

        logger.warning("Amazon review link was not found")
        return {"opened": False, "review_count": fallback_review_count}
    except Exception as exc:
        logger.debug(f"Unable to open the Amazon reviews page: {exc}")
        return {"opened": False, "review_count": None}


def _amazon_scrape_reviews(driver, min_reviews: int, product_name: str) -> List[Dict[str, Any]]:
    """Scrape reviews from an Amazon product or review page."""
    reviews: List[Dict[str, Any]] = []
    seen_reviews = set()
    page = 1

    try:
        while len(reviews) < min_reviews:
            logger.info(f"Scraping Amazon review page {page}")
            review_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-hook='review'], div.review, div.a-section.review")
            logger.info(f"Amazon reviews found: {len(review_elements)}")

            if not review_elements:
                page_review_count = _extract_amazon_review_count(driver)
                fallback_reviews = _extract_amazon_reviews_from_page_source(driver, product_name)
                if fallback_reviews:
                    reviews.extend(fallback_reviews[:min_reviews - len(reviews)])
                    break
                if page_review_count:
                    logger.warning("Amazon review content is blocked on this session; returning a placeholder record with the available review count")
                    return [{
                        "product_name": product_name,
                        "review_text": f"Amazon review content is currently unavailable in this session. The product page reports {page_review_count} reviews.",
                        "rating": 0,
                        "reviewer_name": "System",
                        "review_date": datetime.utcnow().strftime("%Y-%m-%d"),
                        "verified_purchase": False,
                        "platform": "amazon",
                        "helpful_count": 0,
                        "unhelpful_count": 0,
                        "review_url": driver.current_url,
                        "review_count": page_review_count,
                        "review_status": "blocked",
                    }]
                time.sleep(2)
                review_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-hook='review'], div.review, div.a-section.review")

            for element in review_elements:
                if len(reviews) >= min_reviews:
                    break
                try:
                    review = _extract_amazon_review(element, product_name, driver.current_url)
                    if not review:
                        continue
                    review_key = f"{review['review_text'][:80]}|{review['reviewer_name']}"
                    if review_key in seen_reviews:
                        continue
                    seen_reviews.add(review_key)
                    reviews.append(review)
                except Exception as exc:
                    logger.debug(f"Amazon review extraction failed: {exc}")
                    continue

            logger.info(f"Total Amazon reviews collected: {len(reviews)}")
            if len(reviews) >= min_reviews:
                break

            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "li.a-last a")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", next_button)
                page += 1
                time.sleep(4)
            except Exception:
                logger.info("Reached the last review page on Amazon")
                break

    except Exception as exc:
        logger.error(f"Error scraping Amazon reviews: {exc}")

    return reviews[:min_reviews]


def _is_likely_real_review_snippet(snippet: str) -> bool:
    """Return True when a page-source snippet looks like a human-written review."""
    if not snippet:
        return False

    clean_snippet = _clean_text(snippet)
    if not clean_snippet:
        return False

    lowered = clean_snippet.lower()
    if len(clean_snippet) < 25 or len(clean_snippet) > 500:
        return False
    if lowered.count(" ") < 5:
        return False
    if any(token in lowered for token in ["javascript", "https://", "http://", "openid", "signin", "amazon.in", "data-", "var ", "function", "window.", "document"]):
        return False
    if lowered.startswith(("<", "{", "[", "//", "/*")):
        return False
    return True


def _extract_amazon_reviews_from_page_source(driver, product_name: str) -> List[Dict[str, Any]]:
    """Fallback parser that only uses explicit review-like snippets from the page source."""
    try:
        page_source = driver.page_source or ""
        if not page_source:
            return []

        snippets = []
        patterns = [
            r"(?i)(?:review|customer review|verified purchase)[^<]{20,220}",
            r"(?i)(?:best|good|bad|excellent|worth|battery|camera|display|performance)[^<]{20,220}",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, page_source):
                snippet = _clean_text(re.sub(r"<[^>]+>", " ", match.group(0)))
                if _is_likely_real_review_snippet(snippet) and snippet.lower() not in {s.lower() for s in snippets}:
                    snippets.append(snippet)

        if not snippets:
            return []

        reviews = []
        for snippet in snippets[:3]:
            reviews.append({
                "product_name": product_name,
                "review_text": snippet,
                "rating": 0,
                "reviewer_name": "Anonymous",
                "review_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "verified_purchase": "verified purchase" in snippet.lower(),
                "platform": "amazon",
                "helpful_count": 0,
                "unhelpful_count": 0,
                "review_url": driver.current_url,
            })
        return reviews
    except Exception:
        return []


def _extract_amazon_review(element, product_name: str, review_url: str = "") -> Optional[Dict[str, Any]]:
    """Extract a single Amazon review with flexible selectors."""
    try:
        rating = 0
        for selector in [
            "i[data-hook='review-star-rating'] span",
            "i[data-hook='cmps-review-star-rating'] span",
            "span.a-icon-alt",
        ]:
            try:
                rating_text = element.find_element(By.CSS_SELECTOR, selector).text
                rating = int(float(rating_text.split()[0]))
                break
            except Exception:
                continue

        reviewer = "Anonymous"
        for selector in ["span.a-profile-name", "a[data-hook='review-author']", ".reviewer"]:
            try:
                reviewer = element.find_element(By.CSS_SELECTOR, selector).text.strip()
                break
            except Exception:
                continue

        review_date = ""
        for selector in ["span[data-hook='review-date']", "span.review-date", ".review-date"]:
            try:
                review_date = element.find_element(By.CSS_SELECTOR, selector).text.strip()
                break
            except Exception:
                continue

        review_text = _extract_text_from_candidates(
            element,
            [
                "span[data-hook='review-body'] span",
                "span[data-hook='review-body']",
                "div[data-hook='review-collapsed'] span",
                ".review-text-content span",
                ".review-text",
                "div.review-text-content",
            ],
        )

        if not review_text:
            review_text = _clean_text(element.text)

        if not review_text or len(review_text) < 10:
            return None

        verified = "verified purchase" in element.text.lower() or "verified" in element.text.lower()

        return {
            "product_name": product_name,
            "review_text": review_text,
            "rating": rating,
            "reviewer_name": reviewer,
            "review_date": review_date or datetime.utcnow().strftime("%Y-%m-%d"),
            "verified_purchase": verified,
            "platform": "amazon",
            "helpful_count": 0,
            "unhelpful_count": 0,
            "review_url": review_url,
        }

    except Exception as exc:
        logger.debug(f"Review extraction error: {exc}")
        return None


# ============================================================================
# FLIPKART SCRAPER
# ============================================================================


def scrape_flipkart(product_name: str, min_reviews: int = 50) -> List[Dict[str, Any]]:
    """Scrape product reviews from Flipkart."""
    logger.info(f"Starting Flipkart scraper for: {product_name}")

    driver = None
    reviews: List[Dict[str, Any]] = []

    try:
        driver = _create_chrome_driver()

        logger.info("Opening Flipkart...")
        driver.get(Config.PLATFORMS["flipkart"]["url"])
        time.sleep(3)

        try:
            close_btn = driver.find_element(By.CLASS_NAME, "_2KpZ6l")
            close_btn.click()
            time.sleep(1)
        except Exception:
            pass

        logger.info(f"Searching for product: {product_name}")
        if not _flipkart_search_and_open_product(driver, product_name):
            logger.warning("No suitable Flipkart product could be opened")
            return []

        time.sleep(3)
        reviews = _flipkart_scrape_reviews(driver, min_reviews, product_name)
        logger.info(f"✓ Scraped {len(reviews)} reviews from Flipkart")

    except TimeoutException as exc:
        logger.error(f"Timeout while scraping Flipkart: {exc}")
    except WebDriverException as exc:
        logger.error(f"WebDriver error: {exc}")
    except Exception as exc:
        logger.error(f"Error scraping Flipkart: {exc}", exc_info=True)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    return reviews


def _flipkart_search_and_open_product(driver, product_name: str) -> bool:
    """Search Flipkart and open the best matching product result."""
    try:
        search_box = WebDriverWait(driver, Config.SCRAPER_EXPLICIT_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='q'], input[title*='Search']"))
        )
        search_box.clear()
        search_box.send_keys(product_name)
        search_box.submit()
        time.sleep(3)

        for _ in range(6):
            products = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/'], a[href*='/itm/']")
            if not products:
                time.sleep(2)
                continue

            for product in products:
                try:
                    href = product.get_attribute("href") or ""
                    if not href or "/p/" not in href and "/itm/" not in href:
                        continue
                    title = (product.text or "").strip()
                    if title and len(products) > 1 and not _looks_like_product_match(title, product_name):
                        continue
                    logger.info("Opening Flipkart product page")
                    driver.get(href)
                    WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    time.sleep(3)
                    return True
                except Exception as exc:
                    logger.debug(f"Flipkart product candidate failed: {exc}")
                    continue

        logger.warning("No suitable Flipkart product result was opened")
        return False
    except TimeoutException:
        logger.error("Search box not found on Flipkart")
        return False


def _flipkart_scrape_reviews(driver, min_reviews: int, product_name: str) -> List[Dict[str, Any]]:
    """Scrape reviews from a Flipkart product page."""
    reviews: List[Dict[str, Any]] = []
    seen_reviews = set()

    try:
        review_count = _extract_flipkart_review_count(driver.page_source or "")
        if review_count:
            logger.info(f"Flipkart page reports {review_count} reviews")

        while len(reviews) < min_reviews:
            review_containers = driver.find_elements(By.CSS_SELECTOR, "div._27M-vq, div._1AtVbE, div[data-testid='review'], div[class*='review']")
            logger.info(f"Flipkart review containers found: {len(review_containers)}")

            if not review_containers:
                logger.info("No Flipkart review containers found; trying structured review data in the page source")
                fallback_reviews = _extract_flipkart_reviews_from_page_source(driver.page_source or "", product_name)
                if fallback_reviews:
                    for fallback_review in fallback_reviews:
                        if len(reviews) >= min_reviews:
                            break
                        review_key = f"{fallback_review['review_text'][:80]}|{fallback_review['reviewer_name']}"
                        if review_key in seen_reviews:
                            continue
                        seen_reviews.add(review_key)
                        reviews.append(fallback_review)
                    if reviews:
                        break
                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(2)
                review_containers = driver.find_elements(By.CSS_SELECTOR, "div._27M-vq, div._1AtVbE, div[data-testid='review'], div[class*='review']")

            for container in review_containers:
                if len(reviews) >= min_reviews:
                    break
                try:
                    review = _extract_flipkart_review(container, product_name)
                    if not review:
                        continue
                    review_key = f"{review['review_text'][:80]}|{review['reviewer_name']}"
                    if review_key in seen_reviews:
                        continue
                    seen_reviews.add(review_key)
                    reviews.append(review)
                except StaleElementReferenceException:
                    continue
                except Exception as exc:
                    logger.debug(f"Error extracting Flipkart review: {exc}")
                    continue

            if len(reviews) >= min_reviews:
                break

            fallback_reviews = _extract_flipkart_reviews_from_page_source(driver.page_source or "", product_name)
            if fallback_reviews and len(reviews) < min_reviews:
                for fallback_review in fallback_reviews:
                    if len(reviews) >= min_reviews:
                        break
                    review_key = f"{fallback_review['review_text'][:80]}|{fallback_review['reviewer_name']}"
                    if review_key in seen_reviews:
                        continue
                    seen_reviews.add(review_key)
                    reviews.append(fallback_review)
                if reviews:
                    break

            logger.info("Scrolling to load more Flipkart reviews...")
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(2)

    except Exception as exc:
        logger.error(f"Error scraping Flipkart reviews: {exc}")

    return reviews[:min_reviews]


def _extract_flipkart_reviews_from_page_source(page_source: str, product_name: str) -> List[Dict[str, Any]]:
    """Extract Flipkart reviews from structured JSON-LD embedded in the page source."""
    reviews: List[Dict[str, Any]] = []
    seen_reviews = set()

    try:
        for match in re.finditer(r"<script[^>]+type=['\"]application/ld\+json['\"][^>]*>(.*?)</script>", page_source, re.IGNORECASE | re.DOTALL):
            payload = match.group(1).strip()
            if not payload:
                continue
            payload = re.sub(r"^<!--|-->$", "", payload).strip()
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                continue
            _collect_flipkart_reviews_from_json(parsed, reviews, seen_reviews, product_name)
    except Exception as exc:
        logger.debug(f"Unable to parse Flipkart review JSON-LD: {exc}")

    return reviews


def _collect_flipkart_reviews_from_json(node: Any, reviews: List[Dict[str, Any]], seen_reviews: set, product_name: str) -> None:
    """Recursively pull review objects from parsed JSON data."""
    if isinstance(node, dict):
        if node.get("@type") == "Review":
            review = _build_flipkart_review_from_json(node, product_name)
            if review:
                review_key = f"{review['review_text'][:80]}|{review['reviewer_name']}"
                if review_key not in seen_reviews:
                    seen_reviews.add(review_key)
                    reviews.append(review)
        for value in node.values():
            _collect_flipkart_reviews_from_json(value, reviews, seen_reviews, product_name)
    elif isinstance(node, list):
        for item in node:
            _collect_flipkart_reviews_from_json(item, reviews, seen_reviews, product_name)


def _build_flipkart_review_from_json(review_data: Dict[str, Any], product_name: str) -> Optional[Dict[str, Any]]:
    """Convert a review object from JSON-LD into the app's review dictionary format."""
    try:
        review_text = review_data.get("reviewBody") or review_data.get("description") or review_data.get("name") or ""
        if not isinstance(review_text, str):
            review_text = str(review_text or "")
        review_text = _clean_text(review_text)
        if not review_text:
            return None

        author = review_data.get("author") or {}
        if isinstance(author, dict):
            reviewer_name = author.get("name") or "Anonymous"
        else:
            reviewer_name = str(author or "Anonymous")

        rating = 0
        rating_data = review_data.get("reviewRating") or {}
        if isinstance(rating_data, dict):
            rating_value = rating_data.get("ratingValue")
        else:
            rating_value = rating_data
        try:
            rating = int(float(rating_value))
        except Exception:
            rating = 0

        return {
            "product_name": product_name,
            "review_text": review_text,
            "rating": rating,
            "reviewer_name": reviewer_name,
            "review_date": review_data.get("datePublished") or datetime.utcnow().strftime("%Y-%m-%d"),
            "verified_purchase": False,
            "platform": "flipkart",
            "helpful_count": 0,
            "unhelpful_count": 0,
            "review_url": "",
        }
    except Exception as exc:
        logger.debug(f"Unable to build Flipkart review from JSON-LD: {exc}")
        return None


def _extract_flipkart_review(element, product_name: str) -> Optional[Dict[str, Any]]:
    """Extract a single Flipkart review."""
    try:
        rating = 0
        for selector in ["div.XQDdHH", "div._3LWZlK", "div[class*='rating']"]:
            try:
                rating_text = element.find_element(By.CSS_SELECTOR, selector).text
                rating = int(float(rating_text.split()[0]))
                break
            except Exception:
                continue

        reviewer = "Anonymous"
        for selector in ["._3sN-yb", "span[class*='name']", ".reviewer"]:
            try:
                reviewer = element.find_element(By.CSS_SELECTOR, selector).text.strip()
                break
            except Exception:
                continue

        review_text = _extract_text_from_candidates(
            element,
            [
                "span[data-hook='review-body'] span",
                "span[data-hook='review-body']",
                "div[data-hook='review-collapsed'] span",
                "div.review-text-content span",
                "span.review-text-content",
                "div[class*='review']",
            ],
        )

        if not review_text:
            review_text = _clean_text(element.text)

        if not review_text or len(review_text) < 10:
            return None

        review_date = ""
        for selector in ["._3d-jg8", "span[class*='date']", ".review-date"]:
            try:
                review_date = element.find_element(By.CSS_SELECTOR, selector).text.strip()
                break
            except Exception:
                continue

        verified = "verified purchase" in element.text.lower() or "verified" in element.text.lower()

        return {
            "product_name": product_name,
            "review_text": review_text,
            "rating": rating,
            "reviewer_name": reviewer,
            "review_date": review_date or datetime.utcnow().strftime("%Y-%m-%d"),
            "verified_purchase": verified,
            "platform": "flipkart",
            "helpful_count": 0,
            "unhelpful_count": 0,
            "review_url": "",
        }

    except Exception as exc:
        logger.debug(f"Error extracting review data: {exc}")
        return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _create_chrome_driver() -> webdriver.Chrome:
    """Create and configure a Selenium Chrome WebDriver."""
    try:
        options = Options()

        if Config.BROWSER_HEADLESS:
            options.add_argument("--headless=new")

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--remote-allow-origins=*")
        options.add_argument(f"--window-size={Config.BROWSER_WINDOW_SIZE[0]},{Config.BROWSER_WINDOW_SIZE[1]}")
        options.add_argument(f"user-agent={Config.BROWSER_USER_AGENT}")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"},
        )
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        driver.set_page_load_timeout(Config.SCRAPER_PAGE_LOAD_TIMEOUT)
        driver.implicitly_wait(Config.SCRAPER_IMPLICIT_WAIT)

        logger.info("✓ Chrome WebDriver created successfully")
        return driver

    except Exception as exc:
        logger.error(f"Failed to create Chrome WebDriver: {exc}")
        raise


def _extract_text_from_candidates(element, selectors: List[str]) -> str:
    """Try several CSS selectors and return the first non-empty text content."""
    for selector in selectors:
        try:
            text = element.find_element(By.CSS_SELECTOR, selector).text
            clean_text = _clean_text(text)
            if clean_text:
                return clean_text
        except Exception:
            continue
    return ""


def _extract_search_result_count(driver) -> Optional[int]:
    """Try to extract the Amazon search result count from the current page."""
    try:
        page_text = _clean_text(driver.page_source or "")
        patterns = [
            r"(\d[\d,\. ]*)\s+results",
            r"(\d[\d,\. ]*)\s+result",
            r"(\d[\d,\. ]*)\s+items",
        ]
        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(",", "").replace(".", "").strip()
                if value.isdigit():
                    return int(value)
        return None
    except Exception:
        return None


def _extract_amazon_review_count(driver) -> Optional[int]:
    """Try to extract the review count from the current Amazon page."""
    try:
        page_text = _clean_text(driver.page_source or "")
        patterns = [
            r"(\d[\d,\. ]*)\s+global\s+ratings",
            r"(\d[\d,\. ]*)\s+ratings",
            r"(\d[\d,\. ]*)\s+customer\s+reviews",
            r"(\d[\d,\. ]*)\s+reviews",
        ]
        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(",", "").replace(".", "").strip()
                if value.isdigit():
                    return int(value)
        return None
    except Exception:
        return None


def _extract_amazon_asin(url: str) -> Optional[str]:
    """Extract an Amazon ASIN from the current page URL."""
    try:
        match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url, re.IGNORECASE)
        if match:
            return match.group(1)
    except Exception:
        return None
    return None


def _extract_flipkart_review_count(page_source: str) -> Optional[int]:
    """Extract the review count from Flipkart's embedded product metadata."""
    try:
        for pattern in [r'"reviewCount"\s*:\s*(\d+)', r'"ratingCount"\s*:\s*(\d+)']:
            match = re.search(pattern, page_source or "")
            if match and match.group(1).isdigit():
                return int(match.group(1))
    except Exception:
        return None
    return None


def _is_amazon_access_blocked(driver) -> bool:
    """Detect when Amazon is showing a sign-in, verification, or challenge page."""
    try:
        current_url = (driver.current_url or "").lower()
        blocked_tokens = ["signin", "sign-in", "verify", "challenge", "captcha", "robot", "ap/signin", "auth"]
        if any(token in current_url for token in blocked_tokens):
            return True

        page_text = _clean_text(driver.page_source or "").lower()
        blocked_markers = [
            "verify your identity",
            "sign in to continue",
            "captcha",
            "robot",
            "challenge",
            "enter the characters you see",
        ]
        return any(marker in page_text for marker in blocked_markers)
    except Exception:
        return False


def _clean_text(text: str) -> str:
    """Normalize text extracted from a webpage."""
    if not text:
        return ""
    text = text.replace("\u200b", "").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _looks_like_product_match(text: str, product_name: str) -> bool:
    """Check whether scraped text looks like a match for the requested product."""
    text_tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    product_tokens = set(re.findall(r"[a-z0-9]+", product_name.lower()))
    if not product_tokens:
        return True
    return len(product_tokens & text_tokens) >= max(1, min(3, len(product_tokens)))


def _scroll_to_reviews(driver, pause_time: float = 1.0):
    """Scroll the current page to make review sections visible."""
    try:
        driver.execute_script("window.scrollBy(0, 3000);")
        time.sleep(pause_time)
    except Exception as exc:
        logger.debug(f"Error scrolling: {exc}")
