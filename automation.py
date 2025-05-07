import logging
import os
import random
import sys
import time
import traceback

from selenium import webdriver
from selenium.common.exceptions import (ElementClickInterceptedException,
                                        NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException, WebDriverException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def random_sleep(min_seconds=2, max_seconds=5):
    sleep_time = random.uniform(min_seconds, max_seconds)
    logger.info(f"Sleeping for {sleep_time:.2f} seconds")
    time.sleep(sleep_time)

def setup_driver():
    try:
        logger.info("Setting up Chrome driver")
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Use a more reliable method to get ChromeDriver
        try:
            # First try using ChromeDriverManager
            driver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriver path: {driver_path}")
            service = Service(driver_path)
        except Exception as e:
            logger.warning(f"ChromeDriverManager failed: {str(e)}")
            # Fallback to direct ChromeDriver if available
            if sys.platform == "win32":
                # Windows
                chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                if os.path.exists(chrome_path):
                    logger.info("Using Chrome from default Windows location")
                    chrome_options.binary_location = chrome_path
            elif sys.platform == "darwin":
                # macOS
                chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                if os.path.exists(chrome_path):
                    logger.info("Using Chrome from default macOS location")
                    chrome_options.binary_location = chrome_path
            elif sys.platform == "linux":
                # Linux
                chrome_path = "/usr/bin/google-chrome"
                if os.path.exists(chrome_path):
                    logger.info("Using Chrome from default Linux location")
                    chrome_options.binary_location = chrome_path
            
            # Try to use Chrome directly without ChromeDriverManager
            service = Service()
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        logger.info("Chrome driver setup successful")
        return driver
    except Exception as e:
        logger.error(f"Error setting up driver: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def login_to_instagram(driver, username, password):
    try:
        logger.info("Navigating to Instagram login page")
        driver.get('https://www.instagram.com/accounts/login/')
        random_sleep(3, 5)

        # Wait for login form and fill credentials
        logger.info("Waiting for login form")
        username_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = driver.find_element(By.NAME, "password")

        logger.info("Entering credentials")
        username_input.clear()
        username_input.send_keys(username)
        random_sleep(1, 2)
        password_input.clear()
        password_input.send_keys(password)
        random_sleep(1, 2)
        
        # Find and click the login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # Wait for login to complete
        logger.info("Waiting for login to complete")
        random_sleep(5, 7)
        
        # Check for login success
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home']"))
            )
            logger.info("Login successful")
            return True
        except TimeoutException:
            logger.error("Login failed - Home icon not found")
            # Check for error messages
            try:
                error_message = driver.find_element(By.ID, "slfErrorAlert")
                logger.error(f"Login error message: {error_message.text}")
            except NoSuchElementException:
                logger.error("No specific error message found")
            return False

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def navigate_to_profile(driver, target_username):
    try:
        logger.info(f"Navigating to profile: {target_username}")
        
        # First try direct URL
        try:
            logger.info("Trying direct URL navigation")
            driver.get(f'https://www.instagram.com/{target_username}/')
            random_sleep(3, 5)
            
            # Check if we're on the profile page
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "header"))
                )
                logger.info("Successfully navigated to profile using direct URL")
                return True
            except TimeoutException:
                logger.info("Direct URL navigation failed, trying search method")
        except WebDriverException:
            logger.info("Direct URL navigation failed, trying search method")
        
        # If direct URL fails, try search
        logger.info("Using search to find profile")
        search_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search']"))
        )
        search_box.clear()
        search_box.send_keys(target_username)
        random_sleep(2, 3)

        # Click on the first search result
        search_result = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[role='link']"))
        )
        search_result.click()
        random_sleep(3, 5)
        
        # Verify we're on the profile page
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "header"))
            )
            logger.info("Successfully navigated to profile using search")
            return True
        except TimeoutException:
            logger.error("Failed to verify profile page")
            return False
            
    except Exception as e:
        logger.error(f"Navigation error: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def like_posts(driver):
    try:
        logger.info("Starting to like posts")
        liked_count = 0
        
        # First, try to find posts on the profile page
        logger.info("Looking for posts on profile page")
        
        # Wait for the page to fully load
        random_sleep(3, 5)
        
        # Try to scroll down to load more posts
        logger.info("Scrolling to load more posts")
        for _ in range(5):  # Increased scroll count to load more posts
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            random_sleep(2, 3)
        
        # Take a screenshot for debugging
        try:
            screenshot_path = "profile_screenshot.png"
            driver.save_screenshot(screenshot_path)
            logger.info(f"Saved screenshot to {screenshot_path}")
        except Exception as e:
            logger.warning(f"Failed to save screenshot: {str(e)}")
        
        # NEW APPROACH: Check if the profile is private
        try:
            private_profile = driver.find_elements(By.XPATH, "//h2[contains(text(), 'Private')]")
            if private_profile:
                logger.error("This is a private profile. Cannot like posts.")
                return 0
        except Exception as e:
            logger.warning(f"Error checking for private profile: {str(e)}")
        
        # NEW APPROACH: Try to find posts using a more direct method
        logger.info("Trying to find posts using direct method")
        
        # Try to find posts using a more direct approach
        try:
            # Try to find posts using the most reliable selectors
            post_selectors = [
                "//div[contains(@class, '_aagw')]",  # Post thumbnails
                "//div[contains(@class, '_aabd')]",  # Post containers
                "//div[contains(@class, '_aagv')]",  # Post grid items
                "//div[contains(@class, 'x1i10hfl')]",  # New Instagram class
                "//div[contains(@class, '_aag')]",  # Any element with _aag in class name
                "//div[contains(@class, '_aab')]",  # Any element with _aab in class name
                "//div[contains(@class, '_aac')]",  # Any element with _aac in class name
                "//div[contains(@class, '_aad')]",  # Any element with _aad in class name
                "//div[contains(@class, '_aae')]",  # Any element with _aae in class name
                "//div[contains(@class, '_aaf')]",  # Any element with _aaf in class name
                "//a[contains(@href, '/p/')]",  # Any link to a post
                "//div[@role='button']",  # Any clickable div
                "//div[contains(@class, 'x1i10hfl')]//a",  # Links in new Instagram class
                "//div[contains(@class, '_aagw')]//a",  # Links in post thumbnails
                "//div[contains(@class, '_aabd')]//a",  # Links in post containers
                "//div[contains(@class, '_aagv')]//a",  # Links in post grid items
                "//div[contains(@class, '_aag')]//a",  # Links in any element with _aag in class name
                "//div[contains(@class, '_aab')]//a",  # Links in any element with _aab in class name
                "//div[contains(@class, '_aac')]//a",  # Links in any element with _aac in class name
                "//div[contains(@class, '_aad')]//a",  # Links in any element with _aad in class name
                "//div[contains(@class, '_aae')]//a",  # Links in any element with _aae in class name
                "//div[contains(@class, '_aaf')]//a"  # Links in any element with _aaf in class name
            ]
            
            posts = []
            for selector in post_selectors:
                try:
                    found_posts = driver.find_elements(By.XPATH, selector)
                    if found_posts:
                        logger.info(f"Found {len(found_posts)} posts using selector: {selector}")
                        posts = found_posts
                        break
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {str(e)}")
            
            if not posts:
                logger.error("No posts found on the profile page")
                return 0
            
            # Try to click each post directly
            logger.info(f"Found {len(posts)} posts to process")
            for i, post in enumerate(posts[:10]):  # Limit to first 10 posts
                try:
                    # Get current URL before clicking
                    current_url = driver.current_url
                    
                    # Try to get the post URL first
                    post_url = None
                    try:
                        # Try to get href attribute
                        post_url = post.get_attribute('href')
                        if not post_url or '/p/' not in post_url:
                            # If no href, try to find a child link
                            try:
                                child_link = post.find_element(By.TAG_NAME, 'a')
                                post_url = child_link.get_attribute('href')
                            except NoSuchElementException:
                                pass
                    except Exception as e:
                        logger.warning(f"Error getting post URL: {str(e)}")
                    
                    # If we have a post URL, navigate directly to it
                    if post_url and '/p/' in post_url:
                        logger.info(f"Navigating directly to post URL: {post_url}")
                        driver.get(post_url)
                        random_sleep(2, 3)
                    else:
                        # Otherwise, click the post
                        logger.info("Clicking post to navigate to it")
                        post.click()
                        random_sleep(2, 3)
                    
                    # Check if URL changed to a post URL
                    new_url = driver.current_url
                    if '/p/' in new_url and new_url != current_url:
                        logger.info(f"Found post URL: {new_url}")
                        
                        # Try to like the post
                        try:
                            # Wait for post to load
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.TAG_NAME, "article"))
                            )
                            
                            # NEW APPROACH: Try to find the like button using multiple methods
                            like_button = None
                            
                            # Method 1: Try to find by aria-label
                            try:
                                like_button = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Like') and not(contains(@aria-label, 'Unlike'))]"))
                                )
                                logger.info("Found like button by aria-label")
                            except TimeoutException:
                                logger.info("Could not find like button by aria-label")
                            
                            # Method 2: Try to find by class name
                            if not like_button:
                                try:
                                    like_button = WebDriverWait(driver, 5).until(
                                        EC.presence_of_element_located((By.XPATH, "//button[contains(@class, '_acan') or contains(@class, '_abl-')]"))
                                    )
                                    logger.info("Found like button by class")
                                except TimeoutException:
                                    logger.info("Could not find like button by class")
                            
                            # Method 3: Try to find by SVG path
                            if not like_button:
                                try:
                                    svg = WebDriverWait(driver, 5).until(
                                        EC.presence_of_element_located((By.XPATH, "//svg[.//path[contains(@d, 'M16.792') or contains(@d, 'M8.389') or contains(@d, 'M12') or contains(@d, 'M21.35') or contains(@d, 'M12.001')]]"))
                                    )
                                    like_button = svg.find_element(By.XPATH, "./ancestor::button")
                                    logger.info("Found like button by SVG path")
                                except (TimeoutException, NoSuchElementException):
                                    logger.info("Could not find like button by SVG path")
                            
                            # Method 4: Try to find by role
                            if not like_button:
                                try:
                                    like_button = WebDriverWait(driver, 5).until(
                                        EC.presence_of_element_located((By.XPATH, "//button[@role='button' and contains(@class, '_acan')]"))
                                    )
                                    logger.info("Found like button by role")
                                except TimeoutException:
                                    logger.info("Could not find like button by role")
                            
                            # Method 5: Try to find by any button with heart icon
                            if not like_button:
                                try:
                                    like_button = WebDriverWait(driver, 5).until(
                                        EC.presence_of_element_located((By.XPATH, "//button[.//svg[contains(@aria-label, 'Like')]]"))
                                    )
                                    logger.info("Found like button by heart icon")
                                except TimeoutException:
                                    logger.info("Could not find like button by heart icon")
                            
                            # NEW METHOD: Try to find any button that might be a like button
                            if not like_button:
                                try:
                                    # Try to find any button that might be a like button
                                    buttons = driver.find_elements(By.TAG_NAME, "button")
                                    for button in buttons:
                                        try:
                                            # Check if the button has an aria-label that contains "Like"
                                            aria_label = button.get_attribute("aria-label")
                                            if aria_label and "Like" in aria_label and "Unlike" not in aria_label:
                                                like_button = button
                                                logger.info("Found like button by checking all buttons")
                                                break
                                        except:
                                            continue
                                except Exception as e:
                                    logger.warning(f"Error finding like button by checking all buttons: {str(e)}")
                            
                            # If we found a like button, try to click it
                            if like_button:
                                # Try multiple methods to click the like button
                                click_success = False
                                
                                # Method 1: Direct click with retry
                                for _ in range(3):
                                    try:
                                        like_button.click()
                                        click_success = True
                                        logger.info("Clicked like button directly")
                                        break
                                    except Exception as e:
                                        logger.warning(f"Direct click attempt failed: {str(e)}")
                                        random_sleep(1, 2)
                                
                                # Method 2: JavaScript click
                                if not click_success:
                                    try:
                                        driver.execute_script("arguments[0].click();", like_button)
                                        click_success = True
                                        logger.info("Clicked like button using JavaScript")
                                    except Exception as e:
                                        logger.warning(f"JavaScript click failed: {str(e)}")
                                
                                # Method 3: Action chains with move and click
                                if not click_success:
                                    try:
                                        actions = ActionChains(driver)
                                        actions.move_to_element(like_button)
                                        actions.click()
                                        actions.perform()
                                        click_success = True
                                        logger.info("Clicked like button using ActionChains")
                                    except Exception as e:
                                        logger.warning(f"ActionChains click failed: {str(e)}")
                                
                                # Method 4: Try to find parent button and click it
                                if not click_success:
                                    try:
                                        parent_button = like_button.find_element(By.XPATH, "./ancestor::button")
                                        parent_button.click()
                                        click_success = True
                                        logger.info("Clicked parent button")
                                    except Exception as e:
                                        logger.warning(f"Parent button click failed: {str(e)}")
                                
                                # Method 5: Try to find any clickable ancestor
                                if not click_success:
                                    try:
                                        clickable_ancestor = like_button.find_element(By.XPATH, "./ancestor::*[@role='button' or @onclick or contains(@class, '_acan')]")
                                        clickable_ancestor.click()
                                        click_success = True
                                        logger.info("Clicked clickable ancestor")
                                    except Exception as e:
                                        logger.warning(f"Clickable ancestor click failed: {str(e)}")
                                
                                # Method 6: Try to find any button on the page and click it
                                if not click_success:
                                    try:
                                        all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                        for button in all_buttons:
                                            try:
                                                button.click()
                                                click_success = True
                                                logger.info("Clicked a button on the page")
                                                break
                                            except:
                                                continue
                                    except Exception as e:
                                        logger.warning(f"All buttons click failed: {str(e)}")
                                
                                # Method 7: NEW - Try to find the like button by its position
                                if not click_success:
                                    try:
                                        # Instagram typically has the like button in a specific position
                                        # Try to find it by its position relative to other elements
                                        article = driver.find_element(By.TAG_NAME, "article")
                                        buttons = article.find_elements(By.TAG_NAME, "button")
                                        if buttons:
                                            # The like button is typically one of the first few buttons
                                            for button in buttons[:3]:
                                                try:
                                                    button.click()
                                                    click_success = True
                                                    logger.info("Clicked button by position")
                                                    break
                                                except:
                                                    continue
                                    except Exception as e:
                                        logger.warning(f"Position-based click failed: {str(e)}")
                                
                                # Method 8: NEW - Try to find the like button by its text content
                                if not click_success:
                                    try:
                                        # Try to find any element with "Like" text
                                        like_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Like')]")
                                        for element in like_elements:
                                            try:
                                                # Try to find a clickable ancestor
                                                clickable = element.find_element(By.XPATH, "./ancestor::button")
                                                clickable.click()
                                                click_success = True
                                                logger.info("Clicked element with 'Like' text")
                                                break
                                            except:
                                                continue
                                    except Exception as e:
                                        logger.warning(f"Text-based click failed: {str(e)}")
                                
                                # Method 9: NEW - Try to find the like button by its HTML structure
                                if not click_success:
                                    try:
                                        # Instagram often has a specific structure for the like button
                                        like_containers = driver.find_elements(By.XPATH, "//div[contains(@class, '_aacl') or contains(@class, '_aaco') or contains(@class, '_aacw')]")
                                        for container in like_containers:
                                            try:
                                                container.click()
                                                click_success = True
                                                logger.info("Clicked like container")
                                                break
                                            except:
                                                continue
                                    except Exception as e:
                                        logger.warning(f"Container-based click failed: {str(e)}")
                                
                                # NEW METHOD: Try to click any element that might be a like button
                                if not click_success:
                                    try:
                                        # Try to find any element that might be a like button
                                        elements = driver.find_elements(By.XPATH, "//*[contains(@class, '_acan') or contains(@class, '_abl-') or contains(@class, '_aacl') or contains(@class, '_aaco') or contains(@class, '_aacw')]")
                                        for element in elements:
                                            try:
                                                element.click()
                                                click_success = True
                                                logger.info("Clicked element that might be a like button")
                                                break
                                            except:
                                                continue
                                    except Exception as e:
                                        logger.warning(f"Error clicking elements that might be like buttons: {str(e)}")
                                
                                # NEW METHOD: Try to click any element that might be a like button by its position
                                if not click_success:
                                    try:
                                        # Try to find any element that might be a like button by its position
                                        # Instagram typically has the like button in a specific position
                                        # Try to find it by its position relative to other elements
                                        article = driver.find_element(By.TAG_NAME, "article")
                                        # Try to find any element that might be a like button
                                        elements = article.find_elements(By.XPATH, ".//*[contains(@class, '_acan') or contains(@class, '_abl-') or contains(@class, '_aacl') or contains(@class, '_aaco') or contains(@class, '_aacw')]")
                                        if not elements:
                                            # If no elements found with those classes, try to find any button
                                            elements = article.find_elements(By.TAG_NAME, "button")
                                        
                                        # Try to click each element
                                        for element in elements:
                                            try:
                                                element.click()
                                                click_success = True
                                                logger.info("Clicked element by position")
                                                break
                                            except:
                                                continue
                                    except Exception as e:
                                        logger.warning(f"Error clicking elements by position: {str(e)}")
                                
                                # NEW METHOD: Try to click any element in the article
                                if not click_success:
                                    try:
                                        # Try to find any element in the article
                                        article = driver.find_element(By.TAG_NAME, "article")
                                        elements = article.find_elements(By.XPATH, ".//*")
                                        
                                        # Try to click each element
                                        for element in elements:
                                            try:
                                                element.click()
                                                click_success = True
                                                logger.info("Clicked element in article")
                                                break
                                            except:
                                                continue
                                    except Exception as e:
                                        logger.warning(f"Error clicking elements in article: {str(e)}")
                                
                                # Verify if the like was successful
                                try:
                                    # Wait for the like button to change to "Unlike"
                                    WebDriverWait(driver, 5).until(
                                        lambda d: any(
                                            "Unlike" in b.get_attribute("aria-label") 
                                            for b in d.find_elements(By.TAG_NAME, "button")
                                        )
                                    )
                                    liked_count += 1
                                    logger.info(f"Successfully liked post, total liked: {liked_count}")
                                except TimeoutException:
                                    logger.warning("Could not verify if post was liked")
                            else:
                                logger.warning("Could not find like button for this post")
                        
                        except Exception as e:
                            logger.error(f"Error liking post: {str(e)}")
                        
                        # Go back to the profile page
                        driver.back()
                        random_sleep(2, 3)
                    else:
                        # If not a post URL, go back
                        driver.back()
                        random_sleep(1, 2)
                except Exception as e:
                    logger.warning(f"Error clicking post {i}: {str(e)}")
                    # Try to go back to profile page
                    try:
                        driver.back()
                        random_sleep(1, 2)
                    except:
                        pass
        
        except Exception as e:
            logger.error(f"Error with direct post clicking: {str(e)}")
        
        # If direct clicking didn't work, try the original method
        if liked_count == 0:
            logger.info("Direct clicking didn't work, trying original method")
            
            # Updated post selectors with more reliable options
            post_selectors = [
                "//article//a[contains(@href, '/p/')]",  # Posts within article
                "//div[contains(@class, 'x1i10hfl')]//a[contains(@href, '/p/')]",  # New Instagram class
                "//div[contains(@class, '_aagv')]//a",  # Post grid items
                "//div[contains(@class, '_aabd')]//a",  # Post containers
                "//div[@role='presentation']//a[contains(@href, '/p/')]",  # Presentation role posts
                "//main//article//a[contains(@href, '/p/')]",  # Main content posts
                "//div[contains(@class, '_aagw')]//a",  # Post thumbnails
                "//div[contains(@class, '_aagx')]//a",  # Another post container
                "//div[contains(@class, '_aagy')]//a",  # Another post container
                "//div[contains(@class, '_aagz')]//a",  # Another post container
                "//div[contains(@class, '_aag')]//a",  # Any element with _aag in class name
                "//div[contains(@class, '_aab')]//a",  # Any element with _aab in class name
                "//div[contains(@class, '_aac')]//a",  # Any element with _aac in class name
                "//div[contains(@class, '_aad')]//a",  # Any element with _aad in class name
                "//div[contains(@class, '_aae')]//a",  # Any element with _aae in class name
                "//div[contains(@class, '_aaf')]//a",  # Any element with _aaf in class name
                "//a[contains(@href, '/p/')]",  # Any link to a post
                "//div[contains(@class, 'x1i10hfl')]",  # New Instagram class without link
                "//div[contains(@class, '_aagw')]",  # Post thumbnails without link
                "//div[contains(@class, '_aabd')]",  # Post containers without link
                "//div[contains(@class, '_aagv')]"  # Post grid items without link
            ]
            
            posts = []
            for selector in post_selectors:
                try:
                    found_posts = driver.find_elements(By.XPATH, selector)
                    if found_posts:
                        logger.info(f"Found {len(found_posts)} posts using selector: {selector}")
                        posts = found_posts
                        break
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {str(e)}")
            
            if not posts:
                logger.error("No posts found on the profile page")
                return 0
            
            # Extract post links
            post_links = []
            for post in posts:
                try:
                    # Try to get href attribute
                    link = post.get_attribute('href')
                    if link and '/p/' in link:
                        post_links.append(link)
                    else:
                        # If no href, try to find a child link
                        try:
                            child_link = post.find_element(By.TAG_NAME, 'a')
                            link = child_link.get_attribute('href')
                            if link and '/p/' in link:
                                post_links.append(link)
                        except NoSuchElementException:
                            # If no child link, try to click the post itself
                            try:
                                post.click()
                                random_sleep(2, 3)
                                # Get the current URL which should be a post URL
                                current_url = driver.current_url
                                if '/p/' in current_url:
                                    post_links.append(current_url)
                                # Go back to the profile
                                driver.back()
                                random_sleep(2, 3)
                            except Exception as e:
                                logger.warning(f"Error clicking post: {str(e)}")
                except Exception as e:
                    logger.warning(f"Error extracting post link: {str(e)}")
            
            if not post_links:
                logger.error("No post links found")
                return 0
            
            logger.info(f"Found {len(post_links)} post links to process")
            
            # Like each post
            for i, link in enumerate(post_links):
                logger.info(f"Processing post {i+1}/{len(post_links)}: {link}")
                try:
                    driver.get(link)
                    random_sleep(2, 3)
                    
                    # Wait for post to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "article"))
                    )
                    
                    # NEW APPROACH: Try to find the like button using multiple methods
                    like_button = None
                    
                    # Method 1: Try to find by aria-label
                    try:
                        like_button = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Like') and not(contains(@aria-label, 'Unlike'))]"))
                        )
                        logger.info("Found like button by aria-label")
                    except TimeoutException:
                        logger.info("Could not find like button by aria-label")
                    
                    # Method 2: Try to find by class name
                    if not like_button:
                        try:
                            like_button = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, '_acan') or contains(@class, '_abl-')]"))
                            )
                            logger.info("Found like button by class")
                        except TimeoutException:
                            logger.info("Could not find like button by class")
                    
                    # Method 3: Try to find by SVG path
                    if not like_button:
                        try:
                            svg = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//svg[.//path[contains(@d, 'M16.792') or contains(@d, 'M8.389') or contains(@d, 'M12') or contains(@d, 'M21.35') or contains(@d, 'M12.001')]]"))
                            )
                            like_button = svg.find_element(By.XPATH, "./ancestor::button")
                            logger.info("Found like button by SVG path")
                        except (TimeoutException, NoSuchElementException):
                            logger.info("Could not find like button by SVG path")
                    
                    # Method 4: Try to find by role
                    if not like_button:
                        try:
                            like_button = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//button[@role='button' and contains(@class, '_acan')]"))
                            )
                            logger.info("Found like button by role")
                        except TimeoutException:
                            logger.info("Could not find like button by role")
                    
                    # Method 5: Try to find by any button with heart icon
                    if not like_button:
                        try:
                            like_button = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//button[.//svg[contains(@aria-label, 'Like')]]"))
                            )
                            logger.info("Found like button by heart icon")
                        except TimeoutException:
                            logger.info("Could not find like button by heart icon")
                    
                    # NEW METHOD: Try to find any button that might be a like button
                    if not like_button:
                        try:
                            # Try to find any button that might be a like button
                            buttons = driver.find_elements(By.TAG_NAME, "button")
                            for button in buttons:
                                try:
                                    # Check if the button has an aria-label that contains "Like"
                                    aria_label = button.get_attribute("aria-label")
                                    if aria_label and "Like" in aria_label and "Unlike" not in aria_label:
                                        like_button = button
                                        logger.info("Found like button by checking all buttons")
                                        break
                                except:
                                    continue
                        except Exception as e:
                            logger.warning(f"Error finding like button by checking all buttons: {str(e)}")
                    
                    # If we found a like button, try to click it
                    if like_button:
                        # Try multiple methods to click the like button
                        click_success = False
                        
                        # Method 1: Direct click with retry
                        for _ in range(3):
                            try:
                                like_button.click()
                                click_success = True
                                logger.info("Clicked like button directly")
                                break
                            except Exception as e:
                                logger.warning(f"Direct click attempt failed: {str(e)}")
                                random_sleep(1, 2)
                        
                        # Method 2: JavaScript click
                        if not click_success:
                            try:
                                driver.execute_script("arguments[0].click();", like_button)
                                click_success = True
                                logger.info("Clicked like button using JavaScript")
                            except Exception as e:
                                logger.warning(f"JavaScript click failed: {str(e)}")
                        
                        # Method 3: Action chains with move and click
                        if not click_success:
                            try:
                                actions = ActionChains(driver)
                                actions.move_to_element(like_button)
                                actions.click()
                                actions.perform()
                                click_success = True
                                logger.info("Clicked like button using ActionChains")
                            except Exception as e:
                                logger.warning(f"ActionChains click failed: {str(e)}")
                        
                        # Method 4: Try to find parent button and click it
                        if not click_success:
                            try:
                                parent_button = like_button.find_element(By.XPATH, "./ancestor::button")
                                parent_button.click()
                                click_success = True
                                logger.info("Clicked parent button")
                            except Exception as e:
                                logger.warning(f"Parent button click failed: {str(e)}")
                        
                        # Method 5: Try to find any clickable ancestor
                        if not click_success:
                            try:
                                clickable_ancestor = like_button.find_element(By.XPATH, "./ancestor::*[@role='button' or @onclick or contains(@class, '_acan')]")
                                clickable_ancestor.click()
                                click_success = True
                                logger.info("Clicked clickable ancestor")
                            except Exception as e:
                                logger.warning(f"Clickable ancestor click failed: {str(e)}")
                        
                        # Method 6: Try to find any button on the page and click it
                        if not click_success:
                            try:
                                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                for button in all_buttons:
                                    try:
                                        button.click()
                                        click_success = True
                                        logger.info("Clicked a button on the page")
                                        break
                                    except:
                                        continue
                            except Exception as e:
                                logger.warning(f"All buttons click failed: {str(e)}")
                        
                        # Method 7: NEW - Try to find the like button by its position
                        if not click_success:
                            try:
                                # Instagram typically has the like button in a specific position
                                # Try to find it by its position relative to other elements
                                article = driver.find_element(By.TAG_NAME, "article")
                                buttons = article.find_elements(By.TAG_NAME, "button")
                                if buttons:
                                    # The like button is typically one of the first few buttons
                                    for button in buttons[:3]:
                                        try:
                                            button.click()
                                            click_success = True
                                            logger.info("Clicked button by position")
                                            break
                                        except:
                                            continue
                            except Exception as e:
                                logger.warning(f"Position-based click failed: {str(e)}")
                        
                        # Method 8: NEW - Try to find the like button by its text content
                        if not click_success:
                            try:
                                # Try to find any element with "Like" text
                                like_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Like')]")
                                for element in like_elements:
                                    try:
                                        # Try to find a clickable ancestor
                                        clickable = element.find_element(By.XPATH, "./ancestor::button")
                                        clickable.click()
                                        click_success = True
                                        logger.info("Clicked element with 'Like' text")
                                        break
                                    except:
                                        continue
                            except Exception as e:
                                logger.warning(f"Text-based click failed: {str(e)}")
                        
                        # Method 9: NEW - Try to find the like button by its HTML structure
                        if not click_success:
                            try:
                                # Instagram often has a specific structure for the like button
                                like_containers = driver.find_elements(By.XPATH, "//div[contains(@class, '_aacl') or contains(@class, '_aaco') or contains(@class, '_aacw')]")
                                for container in like_containers:
                                    try:
                                        container.click()
                                        click_success = True
                                        logger.info("Clicked like container")
                                        break
                                    except:
                                        continue
                            except Exception as e:
                                logger.warning(f"Container-based click failed: {str(e)}")
                        
                        # NEW METHOD: Try to click any element that might be a like button
                        if not click_success:
                            try:
                                # Try to find any element that might be a like button
                                elements = driver.find_elements(By.XPATH, "//*[contains(@class, '_acan') or contains(@class, '_abl-') or contains(@class, '_aacl') or contains(@class, '_aaco') or contains(@class, '_aacw')]")
                                for element in elements:
                                    try:
                                        element.click()
                                        click_success = True
                                        logger.info("Clicked element that might be a like button")
                                        break
                                    except:
                                        continue
                            except Exception as e:
                                logger.warning(f"Error clicking elements that might be like buttons: {str(e)}")
                        
                        # NEW METHOD: Try to click any element that might be a like button by its position
                        if not click_success:
                            try:
                                # Try to find any element that might be a like button by its position
                                # Instagram typically has the like button in a specific position
                                # Try to find it by its position relative to other elements
                                article = driver.find_element(By.TAG_NAME, "article")
                                # Try to find any element that might be a like button
                                elements = article.find_elements(By.XPATH, ".//*[contains(@class, '_acan') or contains(@class, '_abl-') or contains(@class, '_aacl') or contains(@class, '_aaco') or contains(@class, '_aacw')]")
                                if not elements:
                                    # If no elements found with those classes, try to find any button
                                    elements = article.find_elements(By.TAG_NAME, "button")
                                
                                # Try to click each element
                                for element in elements:
                                    try:
                                        element.click()
                                        click_success = True
                                        logger.info("Clicked element by position")
                                        break
                                    except:
                                        continue
                            except Exception as e:
                                logger.warning(f"Error clicking elements by position: {str(e)}")
                        
                        # NEW METHOD: Try to click any element in the article
                        if not click_success:
                            try:
                                # Try to find any element in the article
                                article = driver.find_element(By.TAG_NAME, "article")
                                elements = article.find_elements(By.XPATH, ".//*")
                                
                                # Try to click each element
                                for element in elements:
                                    try:
                                        element.click()
                                        click_success = True
                                        logger.info("Clicked element in article")
                                        break
                                    except:
                                        continue
                            except Exception as e:
                                logger.warning(f"Error clicking elements in article: {str(e)}")
                        
                        # Verify if the like was successful
                        try:
                            # Wait for the like button to change to "Unlike"
                            WebDriverWait(driver, 5).until(
                                lambda d: any(
                                    "Unlike" in b.get_attribute("aria-label") 
                                    for b in d.find_elements(By.TAG_NAME, "button")
                                )
                            )
                            liked_count += 1
                            logger.info(f"Successfully liked post {i+1}, total liked: {liked_count}")
                        except TimeoutException:
                            logger.warning(f"Could not verify if post {i+1} was liked")
                    else:
                        logger.info(f"Post {i+1} already liked or like button not found")
                    
                except Exception as e:
                    logger.error(f"Error processing post {i+1}: {str(e)}")
                    continue

        logger.info(f"Finished liking posts. Total liked: {liked_count}")
        return liked_count
    except Exception as e:
        logger.error(f"Like posts error: {str(e)}")
        logger.error(traceback.format_exc())
        return 0

def start_like_automation(your_username, your_password, target_username):
    driver = None
    try:
        logger.info(f"Starting automation for target: {target_username}")
        driver = setup_driver()
        
        # Login to Instagram
        logger.info("Attempting to login")
        if not login_to_instagram(driver, your_username, your_password):
            return "Failed to login to Instagram. Please check your credentials."

        # Navigate to target profile
        logger.info("Attempting to navigate to target profile")
        if not navigate_to_profile(driver, target_username):
            return "Failed to navigate to target profile."

        # Like posts
        logger.info("Starting to like posts")
        liked_count = like_posts(driver)
        
        if liked_count == 0:
            return f"No posts were liked on {target_username}'s profile. This could be because the profile is private, has no posts, or the posts are not accessible."
        
        return f"Successfully liked {liked_count} posts on {target_username}'s profile!"

    except Exception as e:
        logger.error(f"Automation error: {str(e)}")
        logger.error(traceback.format_exc())
        return f"An error occurred: {str(e)}"
    
    finally:
        if driver:
            logger.info("Closing browser")
            driver.quit() 