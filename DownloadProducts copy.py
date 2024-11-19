import os
import csv
import requests
import random
import string
import time
import re
import sqlite_utils
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException
from urllib.parse import urlparse, urlunparse, parse_qs



# Constants
MAX_RETRY_ATTEMPTS = 10
MAX_IMAGE_SAVE_RETRIES = 5
MAX_URL_LOAD_RETRIES = 10
images_directory_path = []
size_variants_list = []
size_variants_price_list = []

def retry(func, max_attempts, error_types):
    for attempt in range(max_attempts):
        try:
            return func()
        except error_types as e:
            print(f"Retry {attempt+1}/{max_attempts} - {str(e)}. Retrying in 5 seconds...")
            time.sleep(5)
    if attempt >= max_attempts:
        print("Unable to connect. Quitting...")
        quit()

def get_user_choice():
    choice = input("Do you want to continue (Y/N)? ").strip().lower()
    return choice == 'y'

def clean_image_url(image_url):
    parsed_url = urlparse(image_url)
    query_params = parse_qs(parsed_url.query)
    # Remove 'format' and 'width' parameters if they exist
    query_params.pop('format', None)
    query_params.pop('width', None)
    # Reconstruct the URL without the unwanted parameters
    new_query = '&'.join([f"{key}={value[0]}" for key, value in query_params.items()])
    cleaned_url = urlunparse(parsed_url._replace(query=new_query))
    return cleaned_url
    
def download_image(image_url, product_directory, j):
    image_path = ''
    # cleaned_url = clean_image_url(image_url)
    for attempt in range(MAX_IMAGE_SAVE_RETRIES):
        try:
            image_response = requests.get(image_url)
            image_extension = image_url.split('.')[-1]  # Get the file extension from the URL
            image_filename = f"image_{j}.{image_extension}"
            image_path = os.path.join(product_directory, image_filename)
            with open(image_path, 'wb') as image_file:
                image_file.write(image_response.content)
                # images_directory_path.append(image_path)
                # image_path.append(image_path)
            break  # Exit the retry loop if the image is saved successfully
        except Exception as e:
            print(f"Attempt {attempt+1}/{MAX_IMAGE_SAVE_RETRIES} - Error saving image: {str(e)}. Retrying...")
    return image_path
    
def is_image_size_above_threshold(url, threshold):
    response = requests.head(url)
    if 'Content-Length' in response.headers:
        return int(response.headers['Content-Length']) > threshold
    return False

def fetch_product_images(driver, product_directory):
    images_path = []
    # Using the product directory name to filter image elements by their alt attribute
    # product_name = os.path.basename(product_directory)  # Get the product directory name
    # print(product_name)
    # swiper_slides = driver.find_elements(By.CSS_SELECTOR, f'img[alt^="{product_name.split(' ')[0]}"]')
    swiper_slides = driver.find_elements(By.CSS_SELECTOR, 'div.swiper-slide img')
    # Iterate over the found elements
    for slide in swiper_slides:
        if len(images_path) >= 5:  # Limit to 5 images
            break
        img_url = slide.get_attribute('src')
        # Remove the format and width parameters
        clean_url = clean_image_url(img_url)
        # Only consider images with jpeg, jpg, or png formats after cleaning
        if clean_url.endswith(('.jpeg', '.jpg', '.png')):
                # Check if the image size is above 10 KB
                if is_image_size_above_threshold(clean_url, 10240):
                    images_path.append(clean_url)
            # images_path.append(clean_url)
    return images_path

def fetch_desired_container_count(driver):
    try:
        # Wait for the element containing the results count to be present
        result_count_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="searchHeader"] .sc-c7c319e8-4'))
        )
        # Extract the text content of the element
        result_text = result_count_element.text
        # Use a regular expression to find the numeric value
        match = re.search(r'(\d+)', result_text)
        if match:
            desired_container_count = int(match.group(1))
            return desired_container_count
        else:
            print("No numeric value found in the result text.")
            return 0
    except Exception as e:
        print(f"Error fetching the desired container count: {str(e)}")
        return 0
# Create FirefoxOptions and set headless mode
firefox_options = Options()
# firefox_options.add_argument('-headless')

def main(category, sub_category, url, class_name, exchange_rate):
        
    with webdriver.Firefox(options=firefox_options) as driver:
        # Set the page load timeout
        driver.set_page_load_timeout(300)  # Set the timeout in seconds
        
        while True:
            print("Connecting to the database...")
            # Connect to the SQLite database
            db = sqlite_utils.Database("uploaded_products.db")

            # Define the schema for the default_values table
            default_values_table = db.table('default_values', pk='name')
            product_sponsored_name = ''
            # exchange_rate = 0
            # Create a table if it doesn't exist
            if not default_values_table.exists():
                db["default_values"].create({
                    "name": str,
                    "value": str,
                }, pk="name")

            wait = WebDriverWait(driver, 20)

            print("Loading the provided url...")
            retry(
                lambda: driver.get(url),
                MAX_URL_LOAD_RETRIES,
                (WebDriverException, TimeoutException)
            )

            # Wait for a specific count of product containers to be present
            print("Determining the amount of products to expect...\n")
            # wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-qa="select-menu-btn-plp_display"]')))
            # desired_container_count_str = driver.find_elements(By.CSS_SELECTOR, 'span[data-qa="select-menu-btn-label"]')[1].text.split(' ')[0]
            desired_container_count = fetch_desired_container_count(driver)
            print(desired_container_count)
            
            # Maximum number of retries for saving images
            max_image_save_retries = 3

            # Calculate the number of pages to navigate
            print("Calculating the number of pages to navigate...\n")
            while True:
                # Wait for the target element to be clickable and visible
                products_per_page_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-qa="select-menu-btn-plp_display"]')))
                products_per_page = driver.find_elements(By.CSS_SELECTOR,'span[data-qa="select-menu-btn-label"]')[1].text.split(' ')[0]
                if(int(products_per_page) != 150):
                    print("products per page:", products_per_page)
                    print("Changing the amount of products per page")
                    products_per_page_button.click()
                    true_per_page = driver.find_element(By.CSS_SELECTOR, 'li[data-value="150"]')
                    true_per_page.click()
                    time.sleep(5)
                else:
                    print("products per page: 150")
                    break
                
            num_pages = desired_container_count // 150 + (1 if desired_container_count % 150 > 0 else 0)
            print("Number of pages:", num_pages)
            print("Number of pages:", num_pages)
            # Get the product links
            product_links = []
            
            # Iterate through pages
            print("Naviagating through the pages...\n")
            for page_num in range(num_pages):
                # If this is not the first page, navigate to the next page
                if page_num > 0:
                    retry_attempts = 0
                    next_page_button = driver.find_element(By.CSS_SELECTOR, 'img[alt="Next Page"]')
    ##                next_page_link = next_page_button.get_attribute('href')
                    while retry_attempts < 4:
                        try:
                            # Find the "Next Page" button element
                            if next_page_button:
    ##                            driver.get(next_page_link)
                                next_page_button.click()
                                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'productContainer')))
                                break  # Exit the retry loop if the page loads successfully
                            else:
                                print("Next page link not found.")
                        except (WebDriverException, TimeoutException) as e:
                            retry_attempts += 1
                            print(f"Retry {retry_attempts}/3 - Error while loading 'Next Page' link. Retrying in 5 seconds...")
                            time.sleep(5)
                    else:
                        print("Max retry attempts reached. Skipping to the next page...")
                        continue  # Skip to the next page if max retry attempts reached

                print("Counting the number of products to scrap...\n")
                product_containers = driver.find_elements(By.CLASS_NAME, 'productContainer')
                for product in product_containers:
                    try:
                        product_link = product.find_element(By.TAG_NAME, 'a').get_attribute('href')
                        
                        # Check if the product is sponsored (an ad)
                        is_sponsored = False
                        try:
                            sponsored_element = product.find_element(By.CLASS_NAME, class_name)
                            if "sponsored" in sponsored_element.text.lower():
                                print("Found sponsored(ad) product...skipping \n")
                                is_sponsored = True
                        except:
                            pass
                        
                        if not is_sponsored:
                            product_links.append(product_link)
                            
                    except StaleElementReferenceException:
                        pass  # Ignore stale element exceptions

            print("NUMBER OF PRODUCTS TO PROCESS: ", len(product_links))
            
            # Specify the directory to save images and CSV
            base_directory = os.path.join(os.getcwd(), 'ScrapedFiles')
            category_directory = os.path.join(base_directory, category)
            sub_category_directory = os.path.join(category_directory, sub_category)

            # Create the category and sub-category directories if they don't exist
            for directory in [category_directory, sub_category_directory]:
                if not os.path.exists(directory):
                    os.makedirs(directory)

            # Iterate through product links
            for product_link in product_links:
                retry_attempts = 0
                while retry_attempts < 10:  # Maximum number of retry attempts for each product link
                    try:
                        print("Opening link in a new tab...\n")
                        driver.execute_script("window.open(arguments[0], '_blank');", product_link)
                        driver.switch_to.window(driver.window_handles[1])
                        
                        print("Waiting for the product page to load...\n")
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'priceNow')))
                        
                        # Fetch size variations
                        variations = get_variation_data(driver, exchange_rate)
                        if variations['has_variations']:
                            print(f"Available sizes: {variations['sizes']}")
                            print(f"Prices by size: {variations['prices']}")
                            print(f"Stock status: {variations['stock_status']}")
                        
                        # Fetch product details
                        details_page_name = driver.find_element(By.CSS_SELECTOR, 'h1[data-qa^="pdp-name-"]').text
                        brand = driver.find_element(By.CSS_SELECTOR, 'div[data-qa^="pdp-brand-"]').text
                        etb_price = fetch_price(driver, exchange_rate)  # Fetch the base price

                        # Create a directory for the product
                        sanitized_name = re.sub(r'[^a-zA-Z0-9]', '_', details_page_name)[:50]
                        product_directory = os.path.join(sub_category_directory, sanitized_name)
                        
                        # Check if the product directory already exists
                        if os.path.exists(product_directory):
                            print(f"Product '{details_page_name}' already exists. Skipping...")
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                            break  # Skip to the next product link
                        else:
                            # Create the product directory
                            os.makedirs(product_directory)
                            print(f"Created directory for product '{details_page_name}'.")

                        # Fetch product images
                        images_path = fetch_product_images(driver, product_directory)
                        images_directory_path.clear()
                        images_directory_path = ', '.join(images_path)  # Join image paths for CSV

                        if not images_path:
                            # If no images were found, delete the product directory
                            if os.path.exists(product_directory):
                                os.rmdir(product_directory)
                                print(f"No images stored for '{details_page_name}'. Directory deleted.")
                            return None  # Exit the function if no images are found
                        else:
                            # Clear the previous image paths and download new images
                            images_directory_path.clear()
                            for j, image_url in enumerate(images_path):
                                image_path = download_image(image_url, product_directory, j)
                                images_directory_path.append(image_path)

                        # Get the HTML code snippet of the description
                        try:
                            description_element = driver.find_element(By.XPATH, "/html/body/div[1]/div/section/div/div[2]/div[1]/section/div")
                            description_html = description_element.get_attribute("outerHTML")
                        except:
                            description_html = ""

                        # Generate SKU
                        random_letter = random.choice(string.ascii_uppercase)
                        random_number = random.randint(0, 1000000)
                        brand_parts = brand.split(' ')
                        sanitized_brand = brand_parts[0]
                        sku = f"{category[0]}{sub_category[0]}{sanitized_name[0]}_SKU({sanitized_brand}_{random_letter}{random_number})"


                        # Prepare CSV row
                        variant_sizes = ', '.join(variations['sizes'])
                        variant_prices = ', '.join(str(variations['prices'].get(size, 'N/A')) for size in variations['sizes'])
                        # variant_stock_qty = ', '.join(str(variations['stock_status'].get(size, 'N/A')) for size in variations['sizes'])
                        variant_colors = ''  # Assuming no color variations for now

                        csv_header = [
                            'category', 'sub_category', 'brand','name', 'sku', 'description',
                            'availability', 'stock_qty', 'price', 'on_sale', 'sale_price',
                            'recommended', 'tax', 'product_images', 'variant_price', 'variant_stock_qty',
                            'variant_tax', 'variant_Sizes',
                            'variant_Colors'
                        ]
                        csv_row = [
                            category, sub_category, brand, details_page_name, sku, description_html,
                            'in_stock', '100', etb_price, 'FALSE', '',
                            'FALSE', '0.0', images_directory_path, variant_prices, '100',
                            '0.0', variant_sizes,  # Variant sizes
                            variant_colors  # Variant colors
                        ]
                        # Prepare CSV file path
                        csv_file_path = os.path.join(product_directory, 'product_data.csv')
                        # Initialize CSV file if it doesn't exist
                        if not os.path.isfile(csv_file_path):
                            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
                                csv_writer = csv.writer(csv_file)
                                csv_writer.writerow(csv_header)


                        # Write the row to the CSV file
                        with open(csv_file_path, 'a', newline='', encoding='utf-8') as csv_file:
                            csv_writer = csv.writer(csv_file)
                            csv_writer.writerow(csv_row)

                        # Close the product details tab
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        break  # Exit the retry loop if successful
                    except Exception as e:
                        retry_attempts += 1
                        print(f"Retry {retry_attempts}/10 - Error while opening the link: {str(e)}. Retrying in 5 seconds...")
                        time.sleep(5)  # Wait for 5 seconds before retrying
                
                if retry_attempts >= 10:
                    print(f"Max retry attempts reached for product link {product_link}. Moving to the next product...")
                    continue

            print("Script completed successfully.")

def fetch_price(driver, exchange_rate):
    # Wait for price element to be visible and accessible
    wait = WebDriverWait(driver, 10)
    price_element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="div-price-now"]'))
    )
    details_page_price = price_element.text
    extracted_price = details_page_price.split(' ')[1]
    print(extracted_price)
    return float(extracted_price) * int(exchange_rate)

# Try to find the variation tag
def get_variation_data(driver, exchange_rate):
    """
    Fetches size variation data for a product.
    Returns a dictionary containing size variations and their prices.
    """
    wait = WebDriverWait(driver, 10)
    variations_data = {
        'has_variations': False,
        'sizes': [],
        'prices': {},
        'stock_status': {}
    }

    try:
        # Find the size variation element
        variation_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[id^='pdp-variation-']"))
        )
        
        size_header = variation_element.find_element(By.TAG_NAME, "h3")
        
        # Only process if it's a size variation
        if size_header.text == "Size":
            variations_data['has_variations'] = True
            buttons = variation_element.find_elements(By.CSS_SELECTOR, "button")
            processed_sizes = set()  # Track processed sizes
            
            for button in buttons:
                size = button.text
                is_out_of_stock = "has-notification" in button.get_attribute("class")
                is_active = "active" in button.get_attribute("class")
                
                # Check if the size has already been processed
                if size in processed_sizes:
                    continue
                
                variations_data['sizes'].append(size)
                variations_data['stock_status'][size] = not is_out_of_stock

                # Only click if not out of stock and not currently selected
                if not is_out_of_stock and not is_active:
                    try:
                        # Use JavaScript click to avoid potential overlay issues
                        driver.execute_script("arguments[0].click();", button)
                        
                        # Wait for price update
                        wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="div-price-now"]'))
                        )
                        
                        # Get price for this variation
                        price = fetch_price(driver, exchange_rate)
                        variations_data['prices'][size] = price

                        # Mark this size as processed
                        processed_sizes.add(size)

                        # Re-fetch the size variation buttons to reset the state
                        variation_element = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[id^='pdp-variation-']"))
                        )
                        buttons = variation_element.find_elements(By.CSS_SELECTOR, "button")

                    except Exception as e:
                        print(f"Error processing size {size}: {str(e)}")
                        variations_data['prices'][size] = None

            print(f"Found size variations: {variations_data}")
            
        return variations_data

    except Exception as e:
        print(f"Error fetching size variations: {str(e)}")
        return variations_data

if __name__ == "__main__":
    main()
