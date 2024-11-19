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
from selenium.webdriver.common.keys import Keys



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
        
def download_image(image_url, images_path, product_directory, j):
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

def fetch_desired_container_count(driver, count_class_name):
    try:
        # Wait for the element containing the results count to be present
        result_count_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'div[data-qa="searchHeader"] .{count_class_name}'))
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

def main(category, sub_category, url, class_name, count_class_name, exchange_rate):
        
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
            desired_container_count = fetch_desired_container_count(driver, count_class_name)
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
            
            # Specify the directory to save images
            # base_directory = f'C:\\ScrapedFiles'
            base_directory = os.path.join(os.getcwd(), 'ScrapedFiles')
            # base_directory = os.getcwd(),
    ##        down_directory = os.path.join(base_download_directory, base_directory)
            category_directory = os.path.join(base_directory, category)
            sub_category_directory = os.path.join(category_directory, sub_category)

            print("Creating the file path for image storage...\n")
            # Create the category and sub-category directories if they don't exist
            for directory in [category_directory, sub_category_directory]:
                if not os.path.exists(directory):
                    os.makedirs(directory)

            # Counter for total products processed
            total_products_processed = 0

            print("Opening each product one by one to fetch details and get images...\n")
            # Iterate through product links
            for i, product_link in enumerate(product_links):
            
                retry_attempts = 0
                while retry_attempts < 10:  # Maximum number of retry attempts for each product link
                    try:
                        print("Opening link in a new tab...\n")
                        # Open the link in a new tab using JavaScript
                        driver.execute_script("window.open(arguments[0], '_blank');", product_link)
                        
                        # Switch to the new tab
                        driver.switch_to.window(driver.window_handles[1])
                        
                        print("Waiting for the product page to load...\n")
                        # Wait for a maximum of 20 seconds for the page to load
                        try:
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'priceNow')))
                            break  # Exit the retry loop if the page loads successfully
                        except TimeoutException as e:
                            retry_attempts += 1
                            print(f"Retry {retry_attempts}/10 - {str(e)}. Retrying in 5 seconds...")
                            driver.close()  # Close the tab with connection problem
                            time.sleep(5)  # Wait for 5 seconds before retrying
                            driver.switch_to.window(driver.window_handles[0])  # Switch back to the main tab
                    except Exception as e:
                        retry_attempts += 1
                        print(f"Retry {retry_attempts}/10 - Error while opening the link: {str(e)}. Retrying in 5 seconds...")
                        time.sleep(5)  # Wait for 5 seconds before retrying
                
                if retry_attempts >= 10:
                    print(f"Max retry attempts reached for product link {product_link}. Moving to the next product...")
                    driver.switch_to.window(driver.window_handles[0])  # Switch back to the main tab
                    continue
                
                print("Fetching product details(name, price, description)...\n")
                # Retrieve product name and price from the details page
                details_page_name = driver.find_element(By.CSS_SELECTOR, 'h1[data-qa^="pdp-name-"]').text
                details_page_price = driver.find_element(By.CSS_SELECTOR, 'div[data-qa="div-price-now"]').text
                brand = driver.find_element(By.CSS_SELECTOR, 'div[data-qa^="pdp-brand-"]').text
                extracted_price = details_page_price.split(' ')[1]
                print(extracted_price)
                etb_price = float(extracted_price) * int(exchange_rate)
                print(exchange_rate)
                print(etb_price)

                # Get the HTML code snippet of the description
                try:
                    description_element = driver.find_element(By.XPATH, "/html/body/div[1]/div/section/div/div[2]/div[1]/section/div")
                    description_html = description_element.get_attribute("outerHTML")
                except:
                    description_html = ""

                # Sanitize the product name for subdirectory and CSV file creation
                sanitized_name = re.sub(r'[^a-zA-Z0-9]', '_', details_page_name)[:50]
                product_directory = os.path.join(sub_category_directory, sanitized_name)
                    
                # If the product subdirectory already exists, skip to the next product
                if os.path.exists(product_directory):
                    print(f"Product '{details_page_name}' is already saved. Skipping to the next product...")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue
                
                print("Fetching product images...\n")
                # Get the product images
                # wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/section/div/div[1]/div[2]/div/div[1]/div[2]/div/div[1]/div[1]/div/div[1]/div/div/div[1]/div/img')))
                # images_retries = 0
                # image_urls = []
                # while images_retries < max_image_save_retries and not image_urls:
                #     images_container = driver.find_element(By.XPATH, '/html/body/div[1]/div/section/div/div[1]/div[2]/div/div[1]/div[2]/div/div[1]/div[1]/div')
                #     images = images_container.find_elements(By.CLASS_NAME, 'swiper-slide')
                    
                #     image_urls = [image.find_element(By.TAG_NAME, 'img').get_attribute('src').split('?')[0] for image in images]
                
                #     product_images = ','.join(image_urls)
                #     print("NUMBER OF IMAGES:", len(images))
                #     images_retries += 1
                #     if not image_urls:
                #         print(f"Retry {images_retries}/{max_image_save_retries} - Product images not found. Reloading the page...")
                #         driver.refresh()
                #         wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sc-fbb3761a-17')))


                if not os.path.exists(product_directory):
                    os.makedirs(product_directory)
                    print(f"Created directory for product '{details_page_name}'.")
                
                print("Downloading and saving images...\n")
                time.sleep(3)
                # Fetch product images
                image_urls = fetch_product_images(driver, product_directory)
                

                # # Download and save images in the product subdirectory
                # images_path = []
                # max_images_to_save = 5  # Set the maximum number of images to save
                # for j, image_url in enumerate(image_urls):
                #     if j >= max_images_to_save:  # Check if the maximum number of images to save has been reached
                #         break
                #     download_image(image_url, images_path, product_directory,j)

                # Generate a random letter
                random_letter = random.choice(string.ascii_uppercase)

                # Generate a random number between 0 and 1000000
                random_number = random.randint(0, 1000000)
                
                # Calculate SKU
                brand_parts = brand.split(' ')
                sanitized_brand = brand_parts[0]
                sku = f"{category[0]}{sub_category[0]}{sanitized_name[0]}_SKU({sanitized_brand}_{random_letter}{random_number})"

                # Check if any images were stored, if not, delete the directory
                if not image_urls:
                    if os.path.exists(product_directory):
                        os.rmdir(product_directory)
                        print(f"No images stored for '{details_page_name}'. Directory deleted.")
                else:
                    images_directory_path.clear()
                    size_variants_list.clear()
                    size_variants_price_list.clear()
                    for j, image_url in enumerate(image_urls):
                        image_path = download_image(image_url, image_urls, product_directory, j)
                        images_directory_path.append(image_path)
                    # Increment the total products processed counter
                    total_products_processed += 1
                    # variants = get_variation_data(driver, exchange_rate)
                    
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
                            
                            if buttons:  # If buttons exist, use them
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

                                        except Exception as e:
                                            print(f"Error processing size {size}: {str(e)}")
                                            variations_data['prices'][size] = None
                            else:  # If no buttons, try select/dropdown
                                try:
                                    # Find select container
                                    select_container = variation_element.find_element(By.ID, "selectBoxFromComponent")
                                    if not select_container:
                                        select_container = variation_element.find_element(By.CSS_SELECTOR, "[role='combobox']")
                                    
                                    # Click to open dropdown
                                    select_container.click()
                                    time.sleep(1)  # Brief wait for dropdown to open
                                    
                                    # Get all options
                                    options = driver.find_elements(By.CSS_SELECTOR, "[role='option'], [class*='option']")
                                    
                                    for option in options:
                                        is_out_of_stock = "has-notification" in option.get_attribute("class")
                                        if is_out_of_stock:
                                            continue
                                        

                                        size = option.text.strip()
                                        if not size or size in processed_sizes:
                                            continue
                                            
                                        variations_data['sizes'].append(size)
                                        variations_data['stock_status'][size] = True  # Assume in stock for dropdown
                                        
                                        try:
                                            # Click the option
                                            driver.execute_script("arguments[0].click();", option)
                                            time.sleep(1)  # Brief wait for price update
                                            
                                            # Wait for price update
                                            wait.until(
                                                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="div-price-now"]'))
                                            )
                                            
                                            # Get price for this variation
                                            price = fetch_price(driver, exchange_rate)
                                            variations_data['prices'][size] = price
                                            
                                            # Mark this size as processed
                                            processed_sizes.add(size)
                                            
                                            # Reopen dropdown for next iteration
                                            select_container.click()
                                            time.sleep(1)
                                            
                                        except Exception as e:
                                            print(f"Error processing size {size}: {str(e)}")
                                            variations_data['prices'][size] = None
                                            
                                except Exception as e:
                                    print(f"Error processing dropdown: {str(e)}")
                            
                            print(f"Found size variations: {variations_data}")
                            
                        # return variations_data

                    except Exception as e:
                        print(f"Error fetching size variations: {str(e)}")
                        # return variations_data
                    variant_exists = False
                    if variations_data['has_variations']:
                        variant_exists = True
                        # Get the values
                        for size in variations_data['sizes']:
                            if variations_data['stock_status'][size]:
                                size_variants_list.append(str(size))
                                size_variants_price_list.append(str(variations_data['prices'].get(size, etb_price)))
                    print("Creating a file to store product details...\n")
                    # Create a CSV file for storing product information
                    csv_file_path = os.path.join(product_directory, 'product_data.csv')
                    csv_header = [
                        'category', 'sub_category', 'brand', 'tags', 'name', 'sku', 'description', 'manufacture_date',
                        'availability', 'stock_qty', 'weight', 'price', 'on_sale', 'sale_price',
                        'recommended', 'discount', 'block_qty', 'tax', 'product_images',
                        'default','variant_exists', 'variant_sizes', 'variant_prices'
                    ]

                    # Initialize CSV file
                    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow(csv_header)

                        # Create a row for the CSV data
                        csv_row = [
                            category, sub_category, brand, 'Tag 1', details_page_name, sku, description_html, '',
                            'in_stock', '100', '1.0', etb_price, 'FALSE', '',
                            'FALSE', '', '', '0.0', ','.join(images_directory_path),
                            'FALSE', variant_exists, ','.join(size_variants_list), ','.join(size_variants_price_list)
                        ]

                        print("Writing product details to the file created...\n")
                        # Write the row to the CSV file
                        csv_writer.writerow(csv_row)

                print("Closing the product tab opened...\n")
                # Close the product details tab
                driver.close()

                print("Switching back to the main tab...\n")
                # Switch back to the main tab
                driver.switch_to.window(driver.window_handles[0])
            print("\nSummary:")
            print(f"Total products processed: {total_products_processed}")
            print("Number of stored images in each folder:")
            for root, dirs, files in os.walk(sub_category_directory):
                num_images = len([file for file in files if file.startswith("image_")])
                if num_images > 0:
                    print(f"Folder '{os.path.basename(root)}': {num_images} images")

            # Ask for user choice
            choice = get_user_choice()
            if not choice:
                break

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


if __name__ == "__main__":
    main()
