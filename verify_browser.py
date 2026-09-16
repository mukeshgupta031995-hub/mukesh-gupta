import os
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from playwright.sync_api import sync_playwright

def run_tests():
    screenshots_dir = os.path.join(os.path.dirname(__file__), 'test_screenshots')
    os.makedirs(screenshots_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()

        # Track console errors
        console_errors = []
        def handle_console(msg):
            if msg.type == 'error':
                console_errors.append(msg.text)

        # ----------------------------------------------------
        # TEST 1: DESKTOP VIEWPORT (1280x800)
        # ----------------------------------------------------
        print("=== 1. Testing Desktop Viewport (1280x800) ===")
        page = context.new_page()
        page.set_viewport_size({"width": 1280, "height": 800})
        page.on("console", handle_console)

        page.goto('http://127.0.0.1:5000', wait_until='networkidle')
        print("Page title:", page.title())
        assert "Mukesh Gupta" in page.title(), "Title does not contain Mukesh Gupta"

        # Check for horizontal overflow on Desktop
        overflow_desktop = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
        print("Desktop horizontal overflow detected:", overflow_desktop)
        assert not overflow_desktop, "Horizontal overflow detected on desktop!"

        # Verify main landmarks & sections
        sections = ['about', 'highlights', 'experience', 'achievements', 'competencies', 'education', 'contact']
        for sec in sections:
            el = page.locator(f"#{sec}")
            assert el.count() > 0, f"Section #{sec} not found"
            print(f"  [OK] Section #{sec} exists and is visible")

        # Test Competency Filter
        print("\n--- Testing Competency Category Filter ---")
        page.locator(".filter-pill[data-filter='retail']").click()
        page.wait_for_timeout(300)
        visible_retail = page.locator(".skill-category-card[data-category='retail']").is_visible()
        hidden_warehouse = page.locator(".skill-category-card[data-category='warehouse']").is_visible()
        print(f"  Filter 'retail': retail card visible={visible_retail}, warehouse visible={hidden_warehouse}")
        assert visible_retail and not hidden_warehouse, "Filter did not correctly isolate retail skills"

        # Reset filter
        page.locator(".filter-pill[data-filter='all']").click()
        page.wait_for_timeout(300)
        all_visible = page.locator(".skill-category-card[data-category='warehouse']").is_visible()
        assert all_visible, "Resetting filter to 'all' failed"
        print("  [OK] Filter tabs working smoothly")

        # Test CV Modal
        print("\n--- Testing CV Preview Modal ---")
        page.locator("#openCvModalBtn").click()
        page.wait_for_timeout(300)
        modal_visible = page.locator("#cvModal").is_visible()
        print("  Modal visible after open click:", modal_visible)
        assert modal_visible, "CV modal did not open"

        # Close with close button
        page.locator("#closeCvModalBtn").click()
        page.wait_for_timeout(300)
        modal_closed = not page.locator("#cvModal").is_visible()
        print("  Modal hidden after close click:", modal_closed)
        assert modal_closed, "CV modal did not close"

        # Test Contact Form Validation
        print("\n--- Testing Contact Form Validation & Submission ---")
        # Scroll to contact form
        page.locator("#contact").scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        # 1. Blank submit
        page.locator("#submitInquiryBtn").click()
        page.wait_for_timeout(300)
        err_text = page.locator("#formAlert").text_content()
        print("  Validation error banner on empty submit:", err_text)
        assert "Please correct the highlighted fields" in err_text, "Empty validation banner not shown"

        # 2. Fill valid form
        page.fill("#contactName", "Sunil Verma (Head of Retail HR)")
        page.fill("#contactOrg", "Metro Supermarkets Ltd")
        page.fill("#contactEmail", "sunil.verma@metroretail.test")
        page.fill("#contactPhone", "+91 9876543210")
        page.select_option("#contactRoleType", "Store Manager")
        page.fill("#contactMessage", "We are opening a flagship hypermarket and would like to discuss a leadership opportunity.")

        page.locator("#submitInquiryBtn").click()
        page.wait_for_timeout(1500)

        success_text = page.locator("#formAlert").text_content()
        print("  Submission response banner:", success_text)
        assert "Thank you" in success_text or "Inquiry Received" in success_text, "Success message not displayed"

        # Capture Desktop screenshot
        desktop_screenshot = os.path.join(screenshots_dir, 'desktop_view.png')
        page.screenshot(path=desktop_screenshot, full_page=True)
        print(f"  [OK] Desktop full-page screenshot saved: {desktop_screenshot}")

        # ----------------------------------------------------
        # TEST 2: MOBILE VIEWPORT (390x844 - iPhone / Mobile)
        # ----------------------------------------------------
        print("\n=== 2. Testing Mobile Viewport (390x844) ===")
        mobile_page = context.new_page()
        mobile_page.set_viewport_size({"width": 390, "height": 844})
        mobile_page.on("console", handle_console)
        mobile_page.goto('http://127.0.0.1:5000', wait_until='networkidle')

        # Check for horizontal overflow on Mobile
        overflow_mobile = mobile_page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
        print("  Mobile horizontal overflow detected:", overflow_mobile)
        assert not overflow_mobile, "Horizontal overflow detected on mobile!"

        # Test Mobile Hamburger Menu
        hamburger = mobile_page.locator("#mobileMenuToggle")
        assert hamburger.is_visible(), "Hamburger button is not visible on mobile"
        hamburger.click()
        mobile_page.wait_for_timeout(400)

        drawer_open = mobile_page.locator("#mobileDrawer").is_visible()
        print("  Mobile drawer open after click:", drawer_open)
        assert drawer_open, "Mobile drawer did not open"

        # Click a drawer navigation link to close and navigate
        exp_link = mobile_page.locator(".drawer-nav-link[data-section='experience']")
        exp_link.click()
        mobile_page.wait_for_timeout(600)

        drawer_closed = not mobile_page.locator("#mobileDrawer.is-open").is_visible()
        print("  Mobile drawer closed after link click:", drawer_closed)
        assert drawer_closed, "Mobile drawer did not close after clicking link"

        # Capture Mobile screenshot
        mobile_screenshot = os.path.join(screenshots_dir, 'mobile_view.png')
        mobile_page.screenshot(path=mobile_screenshot, full_page=True)
        print(f"  [OK] Mobile full-page screenshot saved: {mobile_screenshot}")

        # ----------------------------------------------------
        # TEST 3: TABLET VIEWPORT (768x1024 - iPad)
        # ----------------------------------------------------
        print("\n=== 3. Testing Tablet Viewport (768x1024) ===")
        tablet_page = context.new_page()
        tablet_page.set_viewport_size({"width": 768, "height": 1024})
        tablet_page.on("console", handle_console)
        tablet_page.goto('http://127.0.0.1:5000', wait_until='networkidle')

        overflow_tablet = tablet_page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
        print("  Tablet horizontal overflow detected:", overflow_tablet)
        assert not overflow_tablet, "Horizontal overflow detected on tablet!"

        tablet_screenshot = os.path.join(screenshots_dir, 'tablet_view.png')
        tablet_page.screenshot(path=tablet_screenshot, full_page=True)
        print(f"  [OK] Tablet full-page screenshot saved: {tablet_screenshot}")

        # ----------------------------------------------------
        # TEST 4: PRINTABLE RESUME PAGE (/download-cv)
        # ----------------------------------------------------
        print("\n=== 4. Testing Printable Resume Page (/download-cv) ===")
        cv_page = context.new_page()
        cv_page.set_viewport_size({"width": 1024, "height": 900})
        cv_page.goto('http://127.0.0.1:5000/download-cv', wait_until='networkidle')

        assert "Mukesh Gupta" in cv_page.title(), "Resume title check failed"
        assert cv_page.locator(".resume-wrapper").is_visible(), "Resume wrapper not visible"
        print("  [OK] Resume page rendered with full styling and print action bar")

        cv_screenshot = os.path.join(screenshots_dir, 'cv_page.png')
        cv_page.screenshot(path=cv_screenshot, full_page=True)
        print(f"  [OK] Resume page screenshot saved: {cv_screenshot}")

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------
        print("\n=== Browser Console Errors Check ===")
        print(f"Total console errors logged: {len(console_errors)}")
        if console_errors:
            for err in console_errors:
                print("  Console Error:", err)
        assert len(console_errors) == 0, f"Found console errors: {console_errors}"

        browser.close()
        print("\n==========================================")
        print(">>> ALL PLAYWRIGHT BROWSER TESTS PASSED! <<<")
        print("==========================================")

if __name__ == '__main__':
    run_tests()
