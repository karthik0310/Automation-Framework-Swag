import os
import re
import pytest
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
    """
    Add browser info to pytest-html metadata (Environment section).
    This will show Browser: chrome/safari in the HTML report.
    """
    browser = config.getoption("--browser")
    if hasattr(config, "_metadata"):
        config._metadata["Browser"] = browser


@pytest.fixture(scope="session")
def browser_name(request):
    """
    Session-level fixture to capture the browser name.
    """
    return request.config.getoption("--browser").lower()


@pytest.fixture
def driver(browser_name):
    print(f"\n[INFO] Running test in browser: {browser_name}")

    remote_url = os.getenv("SELENIUM_REMOTE_URL")

    # ---------------------- CHROME ----------------------
    if browser_name == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")

        # ✅ Docker / Selenium Grid mode
        if remote_url:
            driver = webdriver.Remote(command_executor=remote_url, options=options)
            driver.set_window_size(1920, 1080)

        # ✅ Local execution mode
        else:
            options.add_argument("--start-maximized")
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )

    # ---------------------- SAFARI ----------------------
    elif browser_name == "safari":
        # Safari works only locally on macOS
        driver = webdriver.Safari()
        driver.maximize_window()

    else:
        raise ValueError(f"Unsupported browser: {browser_name}. Use chrome or safari.")

    yield driver
    driver.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    # Capture screenshot for setup or call failure
    if report.when in ("setup", "call") and report.failed:
        driver = item.funcargs.get("driver", None)
        if not driver:
            return

        os.makedirs("screenshots", exist_ok=True)

        safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", item.nodeid)
        screenshot_path = os.path.join("screenshots", f"{safe_name}.png")

        driver.save_screenshot(screenshot_path)

        # Attach screenshot into HTML report
        pytest_html = item.config.pluginmanager.getplugin("html")
        if pytest_html:
            extra = getattr(report, "extra", [])
            extra.append(pytest_html.extras.image(os.path.abspath(screenshot_path)))
            report.extra = extra
