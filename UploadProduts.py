import os
import csv
from selenium import webdriver
import sqlite_utils
from selenium.webdriver.firefox.options import Options
from sqlite_utils.db import NotFoundError
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import time
import random

# Create FirefoxOptions and set headless mode
firefox_options = Options()
# firefox_options.add_argument('-headless')
def main(category,subcategory,max_products):
    # Create or connect to the SQLite database
    db = sqlite_utils.Database('uploaded_products.db')

    # Define the schema for the uploaded products table
    products_table = db.table('uploaded_products', pk='name')

    # Create the table if it doesn't exist
    if not products_table.exists():
        products_table.create({"name": str})
        print(products_table)
    elif products_table.exists():
        print(products_table)
        print(products_table.count)
        for row in products_table.rows:
            print(row)

    # Construct CSV file path based on category and subcategory
    # base_csv_path = 'C:\\ScrapedFiles'  # Replace with your base CSV path
    base_csv_path = os.path.join(os.getcwd(), 'ScrapedFiles')
    subcategory_folder_path = os.path.join(base_csv_path, category, subcategory)

    # Create a Firefox WebDriver instance
    driver = webdriver.Firefox(options=firefox_options)

    # Navigate to the login page and login
    # login_url = 'https://gulit-39295-ruby.b39295.dev.eastus.az.svc.builder.cafe/admin/login'
    login_url = 'https://gulit-39295-ruby.b39295.prod.eastus.az.svc.builder.ai/admin/login'
    
    # Maximum number of retries
    max_retries = 3

    while True:
        retry_count = 0

        # Retry loop
        while retry_count < max_retries:
            try:
                driver.get(login_url)
                break  # Break out of the loop if the operation succeeded
            except Exception as e:
                print(f"An error occurred: {e}")
                retry_count += 1

        # If the loop finished without a successful operation, prompt the user to retry or quit
        if retry_count == max_retries:
            retry_choice = input(f"Failed to load login URL after {max_retries} retries. Retry again? (y/n): ").lower()
            if retry_choice != 'y':
                print("Exiting script.")
                driver.quit()
                exit()
        else:
            break  # Break out of the infinite loop if the operation succeeded

    # Wait for the login elements to load
    wait = WebDriverWait(driver, 10)
    username_field = wait.until(EC.presence_of_element_located((By.ID, 'admin_user_email')))
    password_field = wait.until(EC.presence_of_element_located((By.ID, 'admin_user_password')))
    login_button = wait.until(EC.element_to_be_clickable((By.ID, 'admin_user_submit_action')))

    # Fill in login credentials and login
    username_field = driver.find_element(By.ID, 'admin_user_email')
    password_field = driver.find_element(By.ID, 'admin_user_password')
    login_button = driver.find_element(By.ID, 'admin_user_submit_action')

    username_field.send_keys('abenij09@gmail.com')
    password_field.send_keys('Abenazer@Y0K1$!')
    login_button.click()

    # Wait for login to complete
    wait = WebDriverWait(driver, 60)
    # wait.until(EC.url_contains('https://gulit-39295-ruby.b39295.dev.eastus.az.svc.builder.cafe/admin'))
    wait.until(EC.url_contains('https://gulit-39295-ruby.b39295.prod.eastus.az.svc.builder.ai/admin'))

    # Navigate to the URL of the form
    # form_url = 'https://gulit-39295-ruby.b39295.dev.eastus.az.svc.builder.cafe/admin/products/new'
    form_url = 'https://gulit-39295-ruby.b39295.prod.eastus.az.svc.builder.ai/admin/products/new'
    driver.get(form_url)

    # # Define the path to the file where uploaded product names are tracked
    # uploaded_products_file = os.path.join(base_csv_path, 'uploaded_products.txt')

    # # Create a set to store the names of uploaded products
    # uploaded_product_names = set()

    # # Read already uploaded product names from the file and add to the set
    # if os.path.exists(uploaded_products_file):
    #     with open(uploaded_products_file, 'r') as file:
    #         uploaded_product_names = set(file.read().splitlines())

    product_count = 0

    # Iterate through the subdirectories (folders) in the subcategory folder
    for product_folder in os.listdir(subcategory_folder_path):
        if os.path.isdir(os.path.join(subcategory_folder_path, product_folder)):

    ##        if product_folder in uploaded_product_names or product_count >= max_products:
    ##            if product_count >= max_products:
    ##                print(f"Maximum products ({max_products}) reached. Stopping upload.")
    ##            else:
    ##                print(f"Product '{product_folder}' is already uploaded. Skipping...")
    ##            continue
            
            # Check if the product is already uploaded
            if product_count >= max_products:
                print(f"Maximum products ({max_products}) reached. Stopping upload.")
                exit()  # Exit the script
            else:
                is_uploaded = False
                for row in products_table.rows:
                    if row['name'] == product_folder.replace(' ', '_'):
                        print(f"Product '{product_folder}' is already uploaded. Skipping...")
                        is_uploaded = True
                        break  # Skip to the next product folder
                if is_uploaded:
                    continue  # Continue to the next iteration of the loop
            product_csv_path = os.path.join(subcategory_folder_path, product_folder, 'product_data.csv')
            if not os.path.exists(product_csv_path):
                print(f"Product '{product_folder}' does not have a product_data.csv file. Skipping...")
                continue  # Continue to the next iteration of the loop
            # Define field values from the CSV file
            with open(product_csv_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:

                    category_value = row['category']
                    subcategory_value = row['sub_category']
                    brand_value = row['brand']
                    name_value = row['name']
                    print("NAME:", name_value)
                    sku_value = row['sku']
                    print("SKU:", sku_value)
                    description_value = row['description']
                    availability_value = row['availability']
                    stock_qty_value = row['stock_qty']
                    price_value = row['price']
                    tax_value = row['tax']
                    product_images_value = row['product_images']
                    variant_sizes = row['variant_sizes']
                    variant_prices = row['variant_prices']

                    # # Find the element
                    # element = driver.find_element(By.ID, "master_category_id")
                    # # Scroll the element into view using JavaScript
                    # driver.execute_script("arguments[0].scrollIntoView();", element)
                    # # Selecting Master Category
                    # master_category_dropdown = WebDriverWait(driver, 10).until(
                    #     EC.element_to_be_clickable((By.ID, "master_category_id"))
                    # )
                    # master_category_dropdown.click()

                    # # Typing and selecting option
                    # search_input = driver.find_element(By.CSS_SELECTOR, ".select2-search__field")
                    # # search_input.send_keys("WOMEN")  # Replace with your search term
                    # # Send category letter by letter
                    # for letter in category_value:
                    #     category_input.send_keys(letter)
                    #     time.sleep(0.1)  # Adjust the delay as needed
                    # search_result = WebDriverWait(driver, 10).until(
                    #     EC.element_to_be_clickable((By.XPATH, f'//li[text()="{category_value}"]'))
                    # )
                    # search_result.click()

                    # Find and interact with the dropdowns
                    category_dropdown = driver.find_element(By.CSS_SELECTOR,'span[data-select2-id="1"]')
                    category_dropdown.click()
                    category_input = driver.find_element(By.CSS_SELECTOR, "span.select2-search > input:nth-child(1)")
                    # Clear the existing content in the input field
                    category_input.clear()

                    # Send category letter by letter
                    for letter in category_value:
                        print(category_input)
                        category_input.send_keys(letter)
                        time.sleep(0.1)  # Adjust the delay as needed

                    # Wait for the dropdown options to appear
                    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'select2-results__option--highlighted')))
                    
                    category_result = driver.find_element(By.CLASS_NAME,'select2-results__option--highlighted')
                    category_result.click()

                    subcategory_dropdown = driver.find_element(By.CSS_SELECTOR,'span[data-select2-id="3"]')
                    subcategory_dropdown.click()
                    subcategory_input = driver.find_element(By.CSS_SELECTOR, ".select2-container--focus > span:nth-child(1) > span:nth-child(1) > ul:nth-child(1) > li:nth-child(1) > input:nth-child(1)")
                    
                    # subcategory_dropdown = driver.find_element(By.XPATH,'/html/body/div[1]/div[4]/div/div/form/fieldset[1]/ol/li[2]/span/span[1]/span')
                    # subcategory_dropdown.click()
                    # subcategory_input = driver.find_element(By.XPATH,'/html/body/div[1]/div[4]/div/div/form/fieldset[1]/ol/li[2]/span/span[1]/span/ul/li/input')
                    # Maximum number of retry attempts
                    max_retry_attempts = 3

                    # Retry loop for waiting for dropdown options to appear
                    for attempt in range(max_retry_attempts):   
                        # Clear the existing content in the input field
                        subcategory_input.clear()
                        subcategory_list = subcategory_value.split('.')
                        print("Separated list: ", subcategory_list)

                        for subcategory_ in subcategory_list:
                            # print(subcategory_)
                                
                            # Send category letter by letter
                            for letter in subcategory_:
                                subcategory_input.send_keys(letter)
                                time.sleep(0.2)  # Adjust the delay as needed
                            # Wait for the dropdown options to appear
                            try:
                                wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'select2-results__option--highlighted')))
                                subcategory_result = driver.find_element(By.CLASS_NAME,'select2-results__option--highlighted')
                                subcategory_result.click()
                                # subcategory_list.pop(0)
                            except TimeoutException:      
                                if attempt == max_retry_attempts - 1:
                                    print("Max retry attempts reached. Dropdown options did not appear.")
                                    # Handle the situation where the dropdown options did not appear after multiple retries
                                    # You might choose to log the error or take other actions as needed
                                else:
                                    print("Retry attempt", attempt + 1, "of", max_retry_attempts, ": Dropdown options did not appear. Retrying...")
                                    # Sleep for a moment before the next retry
                                    time.sleep(2)  # You can adjust the delay as needed
                        
                        break


                    brand_dropdown = driver.find_element(By.CSS_SELECTOR,'span[data-select2-id="4"]')
                    brand_dropdown.click()
                    brand_input = driver.find_element(By.CSS_SELECTOR, "span.select2-search > input:nth-child(1)")
                    
                    # brand_dropdown = driver.find_element(By.XPATH,'/html/body/div[1]/div[4]/div/div/form/fieldset[1]/ol/li[3]/span/span[1]/span')
                    # brand_dropdown.click()
                    # brand_input = driver.find_element(By.XPATH,'.select2-container--focus > span:nth-child(1) > span:nth-child(1) > ul:nth-child(1) > li:nth-child(1) > input:nth-child(1)')
                    # Clear the existing content in the input field
                    brand_input.clear()
                    brand_parts = brand_value.split()
                    sanitized_brand = brand_parts[0]
                    # Send category letter by letter
                    for letter in sanitized_brand:
    ##                for letter in brand_parts:
                        brand_input.send_keys(letter)
                        time.sleep(0.1)  # Adjust the delay as needed

                    # Wait for the dropdown options to appear
                    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'select2-results__option--highlighted')))

                    brand_result = driver.find_element(By.CLASS_NAME,'select2-results__option--highlighted')
                    brand_result.click()

                    availability_dropdown = driver.find_element(By.CSS_SELECTOR,'span[data-select2-id="7"]')
                    availability_dropdown.click()
                    availability_input = driver.find_element(By.CSS_SELECTOR,'span.select2-search > input:nth-child(1)')
                    
                    # Clear the existing content in the input field
                    availability_input.clear()

                    # Send category letter by letter
                    for letter in 'in stock':
                        availability_input.send_keys(letter)
                        time.sleep(0.1)  # Adjust the delay as needed

                    # Wait for the dropdown options to appear
                    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'select2-results__option--highlighted')))

                    availability_result = driver.find_element(By.CLASS_NAME,'select2-results__option--highlighted')
                    availability_result.click()

                    #toggle the description between plain text and source code
                    toggle_btn = driver.find_element(By.CLASS_NAME,'cke_toolgroup') 

                    # Find and fill text fields
                    name_field = driver.find_element(By.ID,'catalogue_name')
                    name_field.send_keys(name_value)

                    sku_field = driver.find_element(By.ID,'catalogue_sku')
                    sku_field.send_keys(sku_value)

                    toggle_btn.click()
                    description_field = driver.find_element(By.CSS_SELECTOR,'.cke_source')
                    description_field.send_keys(description_value)

                    stock_qty_field = driver.find_element(By.ID,'catalogue_stock_qty')
                    stock_qty_field.send_keys(stock_qty_value)

                    price_field = driver.find_element(By.ID,'catalogue_price')
                    price_field.send_keys(price_value)
                    
                    tax_dropdown = driver.find_element(By.CSS_SELECTOR,'span[data-select2-id="9"]')
                    tax_dropdown.click()
                    tax_input = driver.find_element(By.CSS_SELECTOR,'span.select2-search > input:nth-child(1)')
                    
                    # Clear the existing content in the input field
                    tax_input.clear()

                    # Send category letter by letter
                    for letter in '0.0':
                        tax_input.send_keys(letter)
                        time.sleep(0.1)  # Adjust the delay as needed

                    # Wait for the dropdown options to appear
                    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'select2-results__option--highlighted')))

                    tax_result = driver.find_element(By.CLASS_NAME,'select2-results__option--highlighted')
                    tax_result.click()


                    # Iterate through the image paths in the 'product_images' column
                    counter = 0
                    image_paths = row['product_images'].split(',')
                    image_paths = image_paths[:5]  # Limit the number of images to 5
                    print("Images Count:", len(image_paths))
                    for image_path in image_paths:
                        # Find the input field for image upload and set the file path
                        add_image_btn = driver.find_element(By.CLASS_NAME,'has_many_add')
                        add_image_btn.click()
                        image_input = driver.find_element(By.XPATH,f'//*[@id="catalogue_attachments_attributes_{counter}_image"]')  # Adjust the XPath as needed
                        image_path = image_path.replace("\\", "\\\\")
                        image_input.send_keys(image_path)
                        counter = counter + 1
                        zoomout = 0
                        zoomout_button = driver.find_element(By.ID,'zoomout')
                        while zoomout<8:
                            zoomout_button.click()
                            zoomout = zoomout + 1
                        crop_button = driver.find_element(By.ID,'replaceCroppedImage')
                        crop_button.click()


                    variant_sizes = row['variant_sizes'].split(',')
                    variant_prices = row['variant_prices'].split(',')
                    variant_exists = row['variant_exists']
                    print(variant_exists)
                    print(len(variant_sizes))
                    print(variant_exists and  len(variant_sizes)>0)
                    if(variant_exists and  len(variant_sizes)>0):
                        print("variant_exists")
                        print(len(variant_sizes))

                        variant_section = driver.find_element(By.CLASS_NAME,'catalogue_variants')
                        for i, size in enumerate(variant_sizes):
                            print("size")
                            print(size)
                            print(len(size))
                            if(size != ''):
                                new_variant_button = variant_section.find_element(By.XPATH, '//a[text()="Add Variant"]')
                                new_variant_button.click()
                        variant_fieldsets = variant_section.find_elements(By.CSS_SELECTOR, 'fieldset.pv_panel')
                        for i, fieldset in enumerate(variant_fieldsets):
                            if(i < len(variant_sizes)-1):
                                checkbox = fieldset.find_elements(By.NAME, 'check_status')
                                checkbox[0].click()
                            new_variant_buttons = fieldset.find_elements(By.XPATH, '//a[text()="Add New Variants"]')
                            new_variant_button = new_variant_buttons[i]
                            new_variant_button.click()
                            variant_select = fieldset.find_element(By.XPATH, f'//span[@aria-labelledby="select2-catalogue_catalogue_variants_attributes_{i}_catalogue_variant_properties_attributes_0_variant_id-container"]')
                            variant_select.click()
                            # variant_size_ul = driver.find_element(By.CSS_SELECTOR, 'ul.select2-results__options')
                            variant_size_ul = driver.find_element(By.ID, f'select2-catalogue_catalogue_variants_attributes_{i}_catalogue_variant_properties_attributes_0_variant_id-results')
                            variant_size_lis = variant_size_ul.find_elements(By.TAG_NAME, 'li')
                            for li in variant_size_lis:
                                if li.text == 'Sizes':
                                    li.click()
                                    break
                            variant_size_select = fieldset.find_element(By.XPATH, f'//span[@aria-labelledby="select2-catalogue_catalogue_variants_attributes_{i}_catalogue_variant_properties_attributes_0_variant_property_id-container"]')
                            variant_size_select.click()
                            size_to_be_entered = variant_sizes[i]
                                                                    
                            size_ul = driver.find_element(By.ID, f'select2-catalogue_catalogue_variants_attributes_{i}_catalogue_variant_properties_attributes_0_variant_property_id-results')
                            size_lis = size_ul.find_elements(By.TAG_NAME, 'li')
                            for li in size_lis:
                                if li.text == size_to_be_entered:
                                    li.click()
                                    break
                            price_input = fieldset.find_element(By.ID, f'catalogue_catalogue_variants_attributes_{i}_price')
                            try:
                                float(variant_prices[i])
                                price_input.send_keys(variant_prices[i])
                            except ValueError:
                                price_input.send_keys(price_value)

                            stock_qty_input = fieldset.find_element(By.ID, f'catalogue_catalogue_variants_attributes_{i}_stock_qty')
                            stock_qty_input.send_keys(stock_qty_value)

                            tax_select = fieldset.find_element(By.XPATH, f'//span[@aria-labelledby="select2-catalogue_catalogue_variants_attributes_{i}_tax_id-container"]')
                            tax_select.click()

                            tax_ul = driver.find_element(By.ID, f'select2-catalogue_catalogue_variants_attributes_{i}_tax_id-results')
                            tax_lis = tax_ul.find_elements(By.TAG_NAME, 'li')
                            for li in tax_lis:
                                if li.text == '0.0':
                                    li.click()
                                    break
                            # checkbox = fieldset.find_element(By.NAME, 'check_status')
                            # checkbox.click()
                            add_image_buttons = fieldset.find_elements(By.XPATH, '//a[text()="Add Image"]')
                            add_image_buttons[i+1].click()
                            image_inputs = driver.find_elements(By.ID, f'catalogue_catalogue_variants_attributes_{i}_attachments_attributes_0_image')
                            # image_input[i].click()
                            random_index = random.randint(0, len(image_paths) - 1)
                            print(random_index)
                            image_path = image_paths[random_index]
                            image_path = image_path.replace("\\", "\\\\")
                            print(image_path)
                            print(len(image_inputs))
                            image_inputs[0].send_keys(image_path)
                            zoomout = 0
                            zoomout_button = driver.find_element(By.ID,'zoomout')
                            while zoomout<8:
                                zoomout_button.click()
                                zoomout = zoomout + 1
                            crop_button = driver.find_element(By.ID,'replaceCroppedImage')
                            crop_button.click()
                        
                    # Find the submit button and click it
                    submit_button = driver.find_element(By.ID,'catalogue_submit_action')
                    submit_button.click()
                    
                    try:
                        # Wait for the success message or page to load
                        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'flash_notice')))
                    except TimeoutException:
                        print("Timed out waiting for success message. Continuing with the next product.")
                        # Check if there was an error message displayed
                        error_message = driver.find_element(By.CLASS_NAME, 'flash_error')
                        if error_message.is_displayed():
                            error_text = error_message.text
                            if "Sku has already been taken" in error_text:
                                print("Error message: SKU has already been taken. Skipping to the next product.")
                            else:
                                print("Error message appeared. There was an issue submitting the form.")
                                
                            # You can add further actions here, like taking a screenshot, logging, etc.
                        else:
                            print("No error message found. Continuing with the next product.")
                    else:
                        # Success message element is visible
                        print("Success message appeared. Product uploaded successfully.")

    ##                # Add the uploaded product name to the set and the file
    ##                uploaded_product_names.add(product_folder)
    ##                with open(uploaded_products_file, 'a') as file:
    ##                    file.write(product_folder + '\n')
                    
                    # Insert the uploaded product into the SQLite database
                    products_table.insert({"name": product_folder})
                    print(f"Product '{product_folder}' inserted into the database.")
                    
                    # Navigate back to the add product form
                    driver.get(form_url)  # Navigating back to the add product form
                    
                    product_count += 1
    # Close the database
    db.close()
    # Close the browser window
    driver.quit()
if __name__ == "__main__":
    main()
