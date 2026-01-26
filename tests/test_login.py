from pages.login_page import LoginPage
from utils.config import BASE_URL, USERS
import logging
logger = logging.getLogger(__name__)


def test_valid_login(driver):
    driver.get(BASE_URL)
    logger.info("Opening Swag Labs")
    login_page = LoginPage(driver)
    login_page.login("standard_user", USERS["standard_user"])

    assert "inventory" in driver.current_url
    logger.info("Login Page Validated")

def test_locked_user_login(driver):
    logger.info("Starting locked user test")

    driver.get(BASE_URL)
    login = LoginPage(driver)

    login.login("locked_out_user", USERS["locked_out_user"])

    error_text = login.get_error_message()
    assert "locked out" in error_text.lower()
