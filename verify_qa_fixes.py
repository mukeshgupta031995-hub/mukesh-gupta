import json
import os
import sys
import math

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from playwright.sync_api import sync_playwright

def calculate_luminance(r, g, b):
    # sRGB linearization
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

def contrast_ratio(l1, l2):
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def parse_rgb(rgb_str):
    # e.g. "rgb(90, 107, 133)" or "rgba(90, 107, 133, 1)"
    import re
    m = re.findall(r'\d+', rgb_str)
    return int(m[0]), int(m[1]), int(m[2])

def run_qa_checks():
    print("==================================================")
    print("STARTING QA FIXES VERIFICATION SUITE")
    print("==================================================")

    # Check inquiries.json is strictly []
    inquiries_path = os.path.join(os.path.dirname(__file__), 'inquiries.json')
    with open(inquiries_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Data Hygiene check: inquiries.json contains {len(data)} records.")
    assert data == [], "inquiries.json is not empty!"
    print("  [PASS] Fix 8: inquiries.json is []")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)

        # ----------------------------------------------------
        # 1. Check SEO Essentials, Favicon, OG Tags, Schema.org
        # ----------------------------------------------------
        page.goto('http://127.0.0.1:5000', wait_until='networkidle')

        # Favicon check
        favicon_href = page.evaluate("() => document.querySelector('link[rel=\"icon\"]')?.getAttribute('href')")
        print("Favicon href:", favicon_href[:60] if favicon_href else None)
        assert favicon_href and "data:image/svg+xml," in favicon_href, "Favicon SVG data URI missing!"
        print("  [PASS] Fix 3.1: Favicon inline SVG present")

        # og:image and og:url check
        og_image = page.evaluate("() => document.querySelector('meta[property=\"og:image\"]')?.getAttribute('content')")
        og_url = page.evaluate("() => document.querySelector('meta[property=\"og:url\"]')?.getAttribute('content')")
        print("og:image:", og_image[:40] + "...")
        print("og:url:", og_url)
        assert og_image and "mukesh-gupta.jpg" in og_image, "og:image missing or incorrect"
        assert og_url and "http" in og_url, "og:url missing or not dynamic"
        print("  [PASS] Fix 3.2: og:image and og:url present")

        # Schema.org JSON-LD check
        ld_json = page.evaluate("""() => {
            const script = document.querySelector('script[type=\"application/ld+json\"]');
            return script ? script.textContent : null;
        }""")
        assert ld_json, "Schema.org script missing"
        schema = json.loads(ld_json)
        assert schema.get("@type") == "Person", "Schema.org @type is not Person"
        assert schema.get("name") == "Mukesh Gupta", "Schema.org name incorrect"
        assert schema.get("worksFor", {}).get("name") == "Reliance Retail Limited", "Schema.org worksFor incorrect"
        print("  [PASS] Fix 3.3: Schema.org Person JSON-LD valid")

        # ----------------------------------------------------
        # 2. Duplicate Heading Semantics (Fix 5)
        # ----------------------------------------------------
        h2_dup = page.evaluate("() => document.querySelector('h2.profile-meta-name')")
        assert h2_dup is None, "Found duplicate h2.profile-meta-name!"
        div_meta = page.evaluate("() => document.querySelector('div.profile-meta-name')?.textContent.trim()")
        assert div_meta == "Mukesh Gupta", f"Expected div.profile-meta-name with 'Mukesh Gupta', got '{div_meta}'"
        print("  [PASS] Fix 5: Duplicate heading converted to div.profile-meta-name")

        # ----------------------------------------------------
        # 3. rel="noopener" on External Links (Fix 4)
        # ----------------------------------------------------
        blank_links = page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[target=\"_blank\"]'));
            return links.map(l => ({
                href: l.getAttribute('href'),
                rel: l.getAttribute('rel'),
                text: l.textContent.trim().substring(0, 30)
            }));
        }""")
        print(f"Checking {len(blank_links)} external-tab links for rel=\"noopener\":")
        for l in blank_links:
            rel = l['rel'] or ''
            print(f"  Link: '{l['text']}' -> rel='{rel}'")
            assert 'noopener' in rel, f"Link {l} is missing rel=\"noopener\"!"
        print("  [PASS] Fix 4: All target='_blank' links have rel='noopener'")

        # ----------------------------------------------------
        # 4. Contrast Check: --outline variable and elements (Fix 1)
        # ----------------------------------------------------
        outline_val = page.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--outline').trim()")
        print("Computed --outline value:", outline_val)
        assert outline_val.lower() == "#5a6b85", f"Expected #5a6b85, got {outline_val}"

        # Test computed styles on .metric-category and .store-kpi-lbl
        metric_color = page.evaluate("() => getComputedStyle(document.querySelector('.metric-category')).color")
        metric_rgb = parse_rgb(metric_color)
        lum_metric = calculate_luminance(*metric_rgb)
        lum_white = calculate_luminance(255, 255, 255)
        cr_white = contrast_ratio(lum_metric, lum_white)
        lum_bg = calculate_luminance(248, 249, 252) # #f8f9fc
        cr_bg = contrast_ratio(lum_metric, lum_bg)
        print(f"Metric Category Color: {metric_color} | Against White: {cr_white:.2f}:1 | Against #f8f9fc: {cr_bg:.2f}:1")
        assert cr_white >= 4.5, f"Contrast against white {cr_white:.2f}:1 fails WCAG AA (>= 4.5:1)"
        assert cr_bg >= 4.5, f"Contrast against bg {cr_bg:.2f}:1 fails WCAG AA (>= 4.5:1)"
        print("  [PASS] Fix 1: Contrast ratio is >= 4.5:1 (WCAG AA passed)")

        # ----------------------------------------------------
        # 5. Icon Font Fallback Resilience CSS Rule (Fix 2)
        # ----------------------------------------------------
        icon_font_family = page.evaluate("() => getComputedStyle(document.querySelector('.material-symbols-outlined')).fontFamily")
        print("Material icon font family:", icon_font_family)
        assert "Material Symbols Outlined" in icon_font_family, "Material Symbols Outlined missing in font-family"
        print("  [PASS] Fix 2: Material symbols fallback CSS rule active")

        # ----------------------------------------------------
        # 6. Breakpoint Overflow Testing (11 Breakpoints)
        # 320, 375, 390, 412, 480, 768, 1024, 1280, 1366, 1440, 1920
        # ----------------------------------------------------
        breakpoints = [320, 375, 390, 412, 480, 768, 1024, 1280, 1366, 1440, 1920]
        print(f"Testing horizontal overflow across {len(breakpoints)} breakpoints...")
        for bp in breakpoints:
            page.set_viewport_size({"width": bp, "height": 800})
            page.wait_for_timeout(100)
            overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
            scroll_w = page.evaluate("() => document.documentElement.scrollWidth")
            inner_w = page.evaluate("() => window.innerWidth")
            assert not overflow, f"Horizontal overflow at {bp}px! scrollWidth={scroll_w}, innerWidth={inner_w}"
            print(f"  [PASS] {bp}px: No overflow (scrollWidth={scroll_w} <= innerWidth={inner_w})")

        # ----------------------------------------------------
        # 7. Focus Trap for Modal (Fix 6)
        # ----------------------------------------------------
        print("\nTesting Focus Trap on CV Modal...")
        page.set_viewport_size({"width": 1280, "height": 800})
        # Focus on the trigger button
        page.focus("#openCvModalBtn")
        trigger_id = page.evaluate("() => document.activeElement?.id")
        assert trigger_id == "openCvModalBtn"

        # Press Enter or click to open modal
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        assert page.locator("#cvModal").is_visible(), "Modal not open"

        # Check that focus is inside modal
        focused_in_modal = page.evaluate("() => document.getElementById('cvModal').contains(document.activeElement)")
        print("  Active element inside modal after open:", focused_in_modal)
        assert focused_in_modal, "Initial focus not moved inside modal"

        # Tab through elements in modal
        modal_focusables = page.evaluate("""() => {
            const m = document.getElementById('cvModal');
            return Array.from(m.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex=\"-1\"])'))
                .filter(el => !el.disabled && el.offsetParent !== null)
                .map(el => el.id || el.className || el.tagName);
        }""")
        print(f"  Found {len(modal_focusables)} focusable elements in modal: {modal_focusables}")

        for step in range(len(modal_focusables) + 2):
            page.keyboard.press("Tab")
            still_in_modal = page.evaluate("() => document.getElementById('cvModal').contains(document.activeElement)")
            assert still_in_modal, f"Focus leaked outside modal on Tab step {step}!"

        # Shift+Tab backwards test
        for step in range(3):
            page.keyboard.press("Shift+Tab")
            still_in_modal = page.evaluate("() => document.getElementById('cvModal').contains(document.activeElement)")
            assert still_in_modal, f"Focus leaked outside modal on Shift+Tab step {step}!"

        print("  [PASS] Focus strictly trapped inside modal during Tab and Shift+Tab")

        # Close modal with close button (click or press Enter when focused)
        page.locator("#closeCvModalBtn").click()
        page.wait_for_timeout(300)
        assert not page.locator("#cvModal").is_visible(), "Modal did not close"

        # Verify focus returned to trigger button
        restored_id = page.evaluate("() => document.activeElement?.id")
        print(f"  Focus restored to element ID: '{restored_id}'")
        assert restored_id == "openCvModalBtn", f"Expected focus to return to 'openCvModalBtn', got '{restored_id}'"
        print("  [PASS] Focus properly returned to trigger button on modal close")

        # ----------------------------------------------------
        # 8. Focus Trap for Mobile Drawer (Fix 6)
        # ----------------------------------------------------
        print("\nTesting Focus Trap on Mobile Drawer...")
        page.set_viewport_size({"width": 390, "height": 844})
        page.focus("#mobileMenuToggle")
        assert page.evaluate("() => document.activeElement?.id") == "mobileMenuToggle"

        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        assert page.locator("#mobileDrawer").is_visible(), "Drawer not open"

        focused_in_drawer = page.evaluate("() => document.getElementById('mobileDrawer').contains(document.activeElement)")
        print("  Active element inside drawer after open:", focused_in_drawer)
        assert focused_in_drawer, "Initial focus not moved inside drawer"

        # Tab through elements in drawer
        drawer_focusables = page.evaluate("""() => {
            const d = document.getElementById('mobileDrawer');
            return Array.from(d.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex=\"-1\"])'))
                .filter(el => !el.disabled && el.offsetParent !== null)
                .map(el => el.id || el.className || el.tagName);
        }""")
        print(f"  Found {len(drawer_focusables)} focusable elements in drawer: {drawer_focusables}")

        for step in range(len(drawer_focusables) + 2):
            page.keyboard.press("Tab")
            still_in_drawer = page.evaluate("() => document.getElementById('mobileDrawer').contains(document.activeElement)")
            assert still_in_drawer, f"Focus leaked outside drawer on Tab step {step}!"

        for step in range(3):
            page.keyboard.press("Shift+Tab")
            still_in_drawer = page.evaluate("() => document.getElementById('mobileDrawer').contains(document.activeElement)")
            assert still_in_drawer, f"Focus leaked outside drawer on Shift+Tab step {step}!"

        print("  [PASS] Focus strictly trapped inside mobile drawer during Tab and Shift+Tab")

        # Close drawer with close button
        page.locator("#closeDrawerBtn").click()
        page.wait_for_timeout(300)
        assert not page.locator("#mobileDrawer.is-open").is_visible(), "Drawer did not close"

        # Verify focus returned to hamburger toggle
        restored_id = page.evaluate("() => document.activeElement?.id")
        print(f"  Focus restored to element ID: '{restored_id}'")
        assert restored_id == "mobileMenuToggle", f"Expected focus to return to 'mobileMenuToggle', got '{restored_id}'"
        print("  [PASS] Focus properly returned to mobileMenuToggle on drawer close")

        # ----------------------------------------------------
        # 9. Console Errors
        # ----------------------------------------------------
        print("\nConsole Errors check:", len(console_errors))
        if console_errors:
            for err in console_errors:
                print("  Console Error:", err)
        assert len(console_errors) == 0, f"Found console errors: {console_errors}"
        print("  [PASS] Zero console errors during entire test run")

        browser.close()

    # Re-verify inquiries.json is still []
    with open(inquiries_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data == [], "inquiries.json was modified during testing!"
    print("  [PASS] inquiries.json is strictly [] after all tests")

    print("\n==================================================")
    print("ALL QA FIXES VERIFIED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    run_qa_checks()
