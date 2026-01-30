import os
import re
import pytest
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        help="Browser to run tests: chrome or safari"
    )


def pytest_configure(config):
    browser = config.getoption("--browser")
    if hasattr(config, "_metadata"):
        config._metadata["Browser"] = browser


@pytest.fixture(scope="session")
def browser_name(request):
    return request.config.getoption("--browser").lower()


@pytest.fixture
def driver(browser_name):
    print(f"\n[INFO] Running test in browser: {browser_name}")

    remote_url = os.getenv("SELENIUM_REMOTE_URL")

    # ---------------------- CHROME ----------------------
    if browser_name == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")

        # ================== GRID / DOCKER MODE ==================
        if remote_url:
            print(f"[INFO] Running on Selenium Grid: {remote_url}")
            driver = webdriver.Remote(
                command_executor=remote_url,
                options=options
            )
            driver.set_window_size(1920, 1080)

        # ================== LOCAL MAC/WINDOWS MODE ==================
        else:
            print("[INFO] Running on Local Chrome")

            driver_path = ChromeDriverManager().install()

            # Fix Mac ARM issue where wrong file is picked
            if "THIRD_PARTY" in driver_path:
                driver_path = str(Path(driver_path).parent / "chromedriver")

            # Ensure executable permission (Mac fix)
            os.chmod(driver_path, 0o755)

            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            driver.maximize_window()

    # ---------------------- SAFARI ----------------------
    elif browser_name == "safari":
        if remote_url:
            raise ValueError("Safari does not support Selenium Grid. Run locally on macOS.")
        print("[INFO] Running on Safari")
        driver = webdriver.Safari()
        driver.maximize_window()

    else:
        raise ValueError(f"Unsupported browser: {browser_name}. Use chrome or safari.")

    yield driver
    driver.quit()


# ---------------------- SCREENSHOT IN HTML REPORT ----------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when in ("setup", "call") and report.failed:
        driver = item.funcargs.get("driver", None)
        if not driver:
            return

        os.makedirs("screenshots", exist_ok=True)

        safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", item.nodeid)
        screenshot_path = os.path.join("screenshots", f"{safe_name}.png")
        driver.save_screenshot(screenshot_path)

        pytest_html = item.config.pluginmanager.getplugin("html")
        if pytest_html:
            extra = getattr(report, "extra", [])
            extra.append(pytest_html.extras.image(os.path.abspath(screenshot_path)))
            report.extra = extra
