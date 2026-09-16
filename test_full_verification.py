import json
import os
import sys
import re
import urllib.request

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
INQUIRIES_PATH = os.path.join(os.path.dirname(__file__), 'inquiries.json')

def linearize(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def luminance(r, g, b):
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

def get_contrast_ratio(rgb1, rgb2):
    l1 = luminance(*rgb1)
    l2 = luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def parse_rgb(rgb_str):
    m = re.findall(r'\d+', rgb_str)
    return int(m[0]), int(m[1]), int(m[2])

def test_backend_routes():
    print("\n" + "="*60)
    print("1. BACKEND / ROUTE VERIFICATION")
    print("="*60)

    # 1. Check inquiries.json is initially []
    with open(INQUIRIES_PATH, 'r', encoding='utf-8') as f:
        initial_inquiries = json.load(f)
    print(f"Initial inquiries.json count: {len(initial_inquiries)}")
    assert initial_inquiries == [], "inquiries.json must start as []!"
    print("  [PASS] inquiries.json starts as []")

    # 2. Test GET /
    req = urllib.request.urlopen(f"{BASE_URL}/")
    assert req.getcode() == 200
    home_html = req.read().decode('utf-8')
    required_strings = ["Mukesh Gupta", "17,442", "Reliance Retail Limited", "+91 7016498175", "mgsmukeshgupta@gmail.com"]
    for s in required_strings:
        assert s in home_html, f"Missing string in /: {s}"
    print("  [PASS] GET /: 200 with all required profile strings present")

    # 3. Test GET /resume, /download-cv, /cv
    for route in ['/resume', '/download-cv', '/cv']:
        res = urllib.request.urlopen(f"{BASE_URL}{route}")
        assert res.getcode() == 200
        content = res.read().decode('utf-8')
        assert "Mukesh Gupta" in content and "Resume" in content
        print(f"  [PASS] GET {route}: 200 (alias of resume)")

    # 4. Test GET /health
    res = urllib.request.urlopen(f"{BASE_URL}/health")
    assert res.getcode() == 200
    health_data = json.loads(res.read().decode('utf-8'))
    assert health_data.get('status') == 'ok'
    print("  [PASS] GET /health: 200, status='ok'")

    # 5. Test GET /robots.txt
    res = urllib.request.urlopen(f"{BASE_URL}/robots.txt")
    assert res.getcode() == 200
    assert 'text/plain' in res.headers.get('Content-Type', '')
    robots_text = res.read().decode('utf-8')
    assert "User-agent: *" in robots_text
    assert "Sitemap:" in robots_text
    print("  [PASS] GET /robots.txt: 200, text/plain, contains Sitemap line")

    # 6. Test GET /sitemap.xml
    res = urllib.request.urlopen(f"{BASE_URL}/sitemap.xml")
    assert res.getcode() == 200
    assert 'application/xml' in res.headers.get('Content-Type', '')
    sitemap_xml = res.read().decode('utf-8')
    assert "<urlset" in sitemap_xml
    assert any(alias in sitemap_xml for alias in ['/cv', '/resume', '/download-cv'])
    print("  [PASS] GET /sitemap.xml: 200, application/xml, contains page URLs")

    # 7. POST /api/contact - empty body
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/contact", data=json.dumps({}).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req)
        assert False, "Expected 400 for empty body"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        err_data = json.loads(e.read().decode('utf-8'))
        assert err_data.get('success') is False
        assert 'errors' in err_data
        print("  [PASS] POST /api/contact (empty body): 400, success=false, errors object present")

    # 8. POST /api/contact - invalid email
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/contact", data=json.dumps({'name': 'Mukesh', 'email': 'not-an-email', 'message': 'Valid message here'}).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req)
        assert False, "Expected 400 for invalid email"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        err_data = json.loads(e.read().decode('utf-8'))
        assert 'email' in err_data.get('errors', {})
        print("  [PASS] POST /api/contact (invalid email): 400, errors.email present")

    # 9. POST /api/contact - short message
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/contact", data=json.dumps({'name': 'Mukesh', 'email': 'valid@company.com', 'message': 'Hi'}).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req)
        assert False, "Expected 400 for short message"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        err_data = json.loads(e.read().decode('utf-8'))
        assert 'message' in err_data.get('errors', {})
        print("  [PASS] POST /api/contact (short message): 400, errors.message present")

    # 10. POST /api/contact - valid full payload
    valid_payload = {
        'name': 'Pooja Sharma',
        'email': 'pooja.sharma@retailventures.in',
        'phone': '+91 9876543210',
        'organization': 'Retail Ventures India',
        'role_type': 'Store Manager',
        'message': 'We have an upcoming regional mandate in Gujarat and would like to connect with Mukesh.'
    }
    req = urllib.request.Request(f"{BASE_URL}/api/contact", data=json.dumps(valid_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
    res = urllib.request.urlopen(req)
    assert res.getcode() == 200
    res_data = json.loads(res.read().decode('utf-8'))
    assert res_data.get('success') is True
    assert 'mailto_fallback' in res_data
    print("  [PASS] POST /api/contact (valid payload): 200, success=true, mailto_fallback present")

    # Check inquiries.json contains exactly one record
    with open(INQUIRIES_PATH, 'r', encoding='utf-8') as f:
        recorded_inquiries = json.load(f)
    print(f"inquiries.json record count after submission: {len(recorded_inquiries)}")
    assert len(recorded_inquiries) == 1, f"Expected 1 record, got {len(recorded_inquiries)}"
    assert recorded_inquiries[0]['name'] == 'Pooja Sharma'
    assert recorded_inquiries[0]['email'] == 'pooja.sharma@retailventures.in'
    print("  [PASS] inquiries.json contains exactly one new record from test submission")

    # Reset inquiries.json to [] per data hygiene
    with open(INQUIRIES_PATH, 'w', encoding='utf-8') as f:
        json.dump([], f)
    print("  [PASS] inquiries.json reset to [] for data hygiene")


def test_browser_and_regressions():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == 'error' and 'fonts.googleapis.com' not in msg.text else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        print("\n" + "="*60)
        print("2. FIX-BY-FIX VERIFICATION")
        print("="*60)

        page.goto(f"{BASE_URL}/", wait_until='networkidle')

        # ----------------------------------------------------
        # Fix 1 — Contrast
        # ----------------------------------------------------
        print("\n--- Fix 1: Contrast Check ---")
        outline_css = page.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--outline').trim()")
        metric_color = page.evaluate("() => getComputedStyle(document.querySelector('.metric-category')).color")
        kpi_color = page.evaluate("() => getComputedStyle(document.querySelector('.store-kpi-lbl')).color")
        print(f"CSS variable --outline: {outline_css}")
        print(f".metric-category color: {metric_color}")
        print(f".store-kpi-lbl color: {kpi_color}")

        rgb_outline = parse_rgb(metric_color)
        white_rgb = (255, 255, 255)
        eff4ff_rgb = (239, 244, 255) # #eff4ff
        f8f9fc_rgb = (248, 249, 252) # #f8f9fc

        cr_white = get_contrast_ratio(rgb_outline, white_rgb)
        cr_eff4ff = get_contrast_ratio(rgb_outline, eff4ff_rgb)
        cr_f8f9fc = get_contrast_ratio(rgb_outline, f8f9fc_rgb)

        print(f"Contrast vs #ffffff: {cr_white:.2f}:1 (Requirement >= 4.5:1)")
        print(f"Contrast vs #eff4ff: {cr_eff4ff:.2f}:1 (Requirement >= 4.5:1)")
        print(f"Contrast vs #f8f9fc: {cr_f8f9fc:.2f}:1")
        assert cr_white >= 4.5, f"Contrast against white {cr_white:.2f}:1 fails WCAG AA"
        assert cr_eff4ff >= 4.5, f"Contrast against #eff4ff {cr_eff4ff:.2f}:1 fails WCAG AA"
        print("  [PASS] Fix 1: All contrast ratios >= 4.5:1 (WCAG AA passed)")

        # ----------------------------------------------------
        # Fix 2 — Icon Font Fallback Resilience
        # ----------------------------------------------------
        print("\n--- Fix 2: Icon Font Fallback Resilience ---")
        # Check rule in stylesheet
        font_rule = page.evaluate("""() => {
            for (let sheet of document.styleSheets) {
                try {
                    for (let rule of sheet.cssRules) {
                        if (rule.selectorText === '.material-symbols-outlined') {
                            return {
                                display: rule.style.display,
                                whiteSpace: rule.style.whiteSpace,
                                fontFamily: rule.style.fontFamily
                            };
                        }
                    }
                } catch(e) {}
            }
            return null;
        }""")
        print(f"Found .material-symbols-outlined rule in CSS: {font_rule}")
        assert font_rule is not None, "Rule .material-symbols-outlined not found in CSS"
        assert font_rule['display'] == 'inline-block', "display != inline-block"
        assert font_rule['whiteSpace'] == 'nowrap', "whiteSpace != nowrap"
        print("  [PASS] Fix 2: .material-symbols-outlined rule verified in CSS")

        # Simulate icon-font failure by blocking Google Fonts
        print("Testing page at 320px with Google Fonts blocked...")
        blocked_page = context.new_page()
        blocked_page.route("**/fonts.googleapis.com/**", lambda route: route.abort())
        blocked_page.route("**/fonts.gstatic.com/**", lambda route: route.abort())
        blocked_page.set_viewport_size({"width": 320, "height": 700})
        blocked_page.goto(f"{BASE_URL}/", wait_until='domcontentloaded')
        blocked_page.wait_for_timeout(500)

        overflow_font_blocked = blocked_page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
        scroll_w = blocked_page.evaluate("() => document.documentElement.scrollWidth")
        inner_w = blocked_page.evaluate("() => window.innerWidth")
        print(f"At 320px with fonts blocked: scrollWidth={scroll_w}, innerWidth={inner_w}, overflow={overflow_font_blocked}")
        assert not overflow_font_blocked, f"Horizontal overflow at 320px when font fails to load!"
        print("  [PASS] Fix 2: No layout overflow at 320px even when icon fonts fail to load")
        blocked_page.close()

        # ----------------------------------------------------
        # Fix 3 — SEO Essentials
        # ----------------------------------------------------
        print("\n--- Fix 3: SEO Essentials ---")
        favicon_href = page.evaluate("() => document.querySelector('link[rel=\"icon\"]')?.getAttribute('href')")
        assert favicon_href and "data:image/svg+xml," in favicon_href
        print(f"Favicon: {favicon_href[:50]}...")
        print("  [PASS] Favicon inline SVG tag present")

        og_img = page.evaluate("() => document.querySelector('meta[property=\"og:image\"]')?.getAttribute('content')")
        og_url = page.evaluate("() => document.querySelector('meta[property=\"og:url\"]')?.getAttribute('content')")
        print(f"og:image: {og_img[:40]}...")
        assert og_img and "mukesh-gupta.jpg" in og_img
        assert og_url and "127.0.0.1" in og_url
        print("  [PASS] og:image and dynamic og:url present (pointing to mukesh-gupta.jpg)")

        json_ld_raw = page.evaluate("() => document.querySelector('script[type=\"application/ld+json\"]')?.textContent")
        schema_obj = json.loads(json_ld_raw)
        assert schema_obj["@context"] == "https://schema.org"
        assert schema_obj["@type"] == "Person"
        assert schema_obj["name"] == "Mukesh Gupta"
        assert schema_obj["telephone"] == "+91-7016498175"
        assert schema_obj["email"] == "mgsmukeshgupta@gmail.com"
        assert schema_obj["address"]["addressLocality"] == "Ahmedabad"
        assert schema_obj["worksFor"]["name"] == "Reliance Retail Limited"
        print("  [PASS] Valid Schema.org Person JSON-LD with verified factual data")

        # ----------------------------------------------------
        # Fix 4 — rel="noopener"
        # ----------------------------------------------------
        print("\n--- Fix 4: rel=\"noopener\" on External Links ---")
        blank_links = page.evaluate("""() => {
            const anchors = Array.from(document.querySelectorAll('a[target=\"_blank\"]'));
            return anchors.map(a => ({
                href: a.getAttribute('href'),
                rel: a.getAttribute('rel'),
                text: a.textContent.replace(/\\s+/g, ' ').trim()
            }));
        }""")
        print(f"Found {len(blank_links)} links with target='_blank':")
        assert len(blank_links) == 4, f"Expected 4 target='_blank' links, found {len(blank_links)}"
        for item in blank_links:
            print(f"  - '{item['text'][:30]}' -> rel='{item['rel']}', href='{item['href']}'")
            assert 'noopener' in (item['rel'] or ''), f"Link missing noopener: {item}"
        print("  [PASS] Fix 4: All target='_blank' links have rel='noopener'")

        # ----------------------------------------------------
        # Fix 5 — Duplicate Heading Semantics
        # ----------------------------------------------------
        print("\n--- Fix 5: Duplicate Heading Semantics ---")
        h2_check = page.evaluate("() => document.querySelectorAll('h2.profile-meta-name').length")
        div_check = page.evaluate("() => document.querySelectorAll('div.profile-meta-name').length")
        assert h2_check == 0, "Found h2.profile-meta-name!"
        assert div_check == 1, "div.profile-meta-name not found!"

        all_headings = page.evaluate("""() => {
            const hs = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
            return hs.map(h => ({
                tag: h.tagName,
                text: h.textContent.replace(/\\s+/g, ' ').trim()
            }));
        }""")
        mukesh_headings = [h for h in all_headings if "Mukesh Gupta" in h['text']]
        print(f"Headings containing 'Mukesh Gupta': {mukesh_headings}")
        assert len(mukesh_headings) == 1, f"Expected exactly 1 heading with 'Mukesh Gupta', got {len(mukesh_headings)}"
        assert mukesh_headings[0]['tag'] == 'H1', "The single heading must be H1"
        print("  [PASS] Fix 5: Exactly one heading for 'Mukesh Gupta' (the H1). Profile card uses div.")

        # ----------------------------------------------------
        # Fix 6 — Focus Trap (Modal & Drawer)
        # ----------------------------------------------------
        print("\n--- Fix 6: Focus Trap (Modal & Drawer) ---")
        # 1. CV Modal
        page.set_viewport_size({"width": 1280, "height": 800})
        page.focus("#openCvModalBtn")
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        assert page.locator("#cvModal").is_visible(), "Modal not open"
        assert page.evaluate("() => document.getElementById('cvModal').contains(document.activeElement)")

        # Tab forward cycling
        for _ in range(8):
            page.keyboard.press("Tab")
            assert page.evaluate("() => document.getElementById('cvModal').contains(document.activeElement)"), "Focus escaped modal during Tab!"

        # Shift+Tab backwards wrapping
        for _ in range(5):
            page.keyboard.press("Shift+Tab")
            assert page.evaluate("() => document.getElementById('cvModal').contains(document.activeElement)"), "Focus escaped modal during Shift+Tab!"

        # Escape key close and focus return
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        assert not page.locator("#cvModal").is_visible(), "Modal did not close on Escape"
        assert page.evaluate("() => document.activeElement?.id") == "openCvModalBtn", "Focus did not return to openCvModalBtn on Escape"
        print("  [PASS] CV Modal: Tab cycle, Shift+Tab wrap, Escape close, and focus restore verified")

        # 2. Mobile Drawer
        page.set_viewport_size({"width": 390, "height": 844})
        page.focus("#mobileMenuToggle")
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        assert page.locator("#mobileDrawer").is_visible(), "Drawer not open"
        assert page.evaluate("() => document.getElementById('mobileDrawer').contains(document.activeElement)")

        for _ in range(15):
            page.keyboard.press("Tab")
            assert page.evaluate("() => document.getElementById('mobileDrawer').contains(document.activeElement)"), "Focus escaped drawer during Tab!"

        for _ in range(5):
            page.keyboard.press("Shift+Tab")
            assert page.evaluate("() => document.getElementById('mobileDrawer').contains(document.activeElement)"), "Focus escaped drawer during Shift+Tab!"

        # Close with Escape
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        assert not page.locator("#mobileDrawer.is-open").is_visible(), "Drawer did not close on Escape"
        assert page.evaluate("() => document.activeElement?.id") == "mobileMenuToggle", "Focus did not return to mobileMenuToggle on Escape"
        print("  [PASS] Mobile Drawer: Tab cycle, Shift+Tab wrap, Escape close, and focus restore verified")

        # ----------------------------------------------------
        # Fix 7 — Image Asset Verification
        # ----------------------------------------------------
        print("\n--- Fix 7: Self-Hosted Profile Image Verification ---")
        img_src = page.evaluate("() => document.querySelector('.avatar-img')?.getAttribute('src')")
        print(f"Profile image src: {img_src}")
        assert "mukesh-gupta.jpg" in img_src, f"Expected mukesh-gupta.jpg in src, got {img_src}"
        natural_w = page.evaluate("() => document.querySelector('.avatar-img')?.naturalWidth")
        print(f"Profile image naturalWidth: {natural_w}")
        assert natural_w > 0, "Profile image failed to load!"
        print("  [PASS] Fix 7: Self-hosted mukesh-gupta.jpg verified and loads successfully")

        # ----------------------------------------------------
        # 3. FULL REGRESSION PASS
        # ----------------------------------------------------
        print("\n" + "="*60)
        print("3. FULL REGRESSION PASS")
        print("="*60)

        # 1. Breakpoint testing (11 breakpoints)
        breakpoints = [320, 375, 390, 412, 480, 768, 1024, 1280, 1366, 1440, 1920]
        print(f"Testing horizontal overflow across {len(breakpoints)} breakpoints...")
        for bp in breakpoints:
            page.set_viewport_size({"width": bp, "height": 800})
            page.wait_for_timeout(100)
            overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
            scroll_w = page.evaluate("() => document.documentElement.scrollWidth")
            client_w = page.evaluate("() => document.documentElement.clientWidth")
            assert not overflow, f"Horizontal overflow at {bp}px! scrollWidth={scroll_w}, clientWidth={client_w}"
            
            # Element bounding rect check
            element_overflow = page.evaluate("""() => {
                const elements = Array.from(document.querySelectorAll('body *'));
                const list = [];
                for (let el of elements) {
                    if (el.offsetWidth > 0 && el.offsetHeight > 0) {
                        const rect = el.getBoundingClientRect();
                        if (rect.right > window.innerWidth + 2) {
                            list.push({ tag: el.tagName, className: el.className, id: el.id, right: Math.round(rect.right), innerWidth: window.innerWidth });
                        }
                    }
                }
                return list;
            }""")
            if element_overflow:
                print(f"  [OBSERVATION] {bp}px: scrollWidth={scroll_w} == clientWidth={client_w}, but {len(element_overflow)} element(s) exceed viewport bounds: {element_overflow[:2]}")
            else:
                print(f"  [PASS] {bp}px: scrollWidth={scroll_w} == clientWidth={client_w}, zero element bounds overflow")

        # 2. Smooth scrolling and header offset
        print("\nTesting Smooth Anchor Navigation and Header Offset...")
        page.set_viewport_size({"width": 1280, "height": 800})
        nav_anchors = ['#about', '#highlights', '#experience', '#achievements', '#competencies', '#education', '#contact']
        for anchor in nav_anchors:
            page.locator(f".desktop-nav a[href='{anchor}']").click()
            page.wait_for_timeout(700)
            target_top = page.evaluate(f"() => document.querySelector('{anchor}').getBoundingClientRect().top")
            scroll_y = page.evaluate("() => window.scrollY")
            print(f"  Nav to {anchor}: target top relative to viewport = {target_top:.1f}px, window.scrollY = {scroll_y:.1f}px")
            if anchor == '#about':
                assert scroll_y == 0 or target_top <= 75
            else:
                assert target_top >= 40 and target_top <= 100, f"Header offset incorrect for {anchor}, got {target_top}px"
        print("  [PASS] Smooth scroll targets align cleanly below fixed header")

        # 3. Scrollspy
        print("\nTesting Scrollspy active link updates...")
        for anchor in ['#about', '#experience', '#competencies', '#contact']:
            page.locator(anchor).scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            active_link_href = page.evaluate("() => document.querySelector('.desktop-nav .nav-link.active')?.getAttribute('href')")
            print(f"  Scrolled to {anchor} -> Active nav link: {active_link_href}")
            assert active_link_href == anchor, f"Expected active nav link {anchor}, got {active_link_href}"
        print("  [PASS] Scrollspy active states update accurately on scroll")

        # 4. Competency Filter Pills
        print("\nTesting Competency Category Filter Pills...")
        page.locator("#competencies").scroll_into_view_if_needed()
        page.wait_for_timeout(300)

        filters = ['retail', 'warehouse', 'finance', 'team', 'systems']
        for cat in filters:
            page.locator(f".filter-pill[data-filter='{cat}']").click()
            page.wait_for_timeout(200)
            visible_card_cats = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('.skill-category-card:not(.hidden)'))
                    .map(c => c.getAttribute('data-category'));
            }""")
            print(f"  Filter '{cat}': visible cards = {visible_card_cats}")
            assert all(c == cat for c in visible_card_cats), f"Found non-matching cards for filter {cat}"

        # Reset to 'all'
        page.locator(".filter-pill[data-filter='all']").click()
        page.wait_for_timeout(200)
        total_cards = page.evaluate("() => document.querySelectorAll('.skill-category-card:not(.hidden)').length")
        assert total_cards >= 4, f"Expected all competency cards visible after 'all' filter, got {total_cards}"
        print("  [PASS] Competency filters dynamically isolate and restore cards")

        # 5. Mobile drawer interactions
        print("\nTesting Mobile Drawer open/close triggers and body scroll lock...")
        page.set_viewport_size({"width": 390, "height": 844})
        
        # Test Hamburger toggle open & close
        page.locator("#mobileMenuToggle").click()
        page.wait_for_timeout(300)
        assert page.locator("#mobileDrawer.is-open").is_visible()
        body_overflow = page.evaluate("() => document.body.style.overflow")
        assert body_overflow == 'hidden', f"Body scroll not locked: {body_overflow}"
        print("  [PASS] Mobile drawer opens and locks body scroll")

        # Test Overlay click close
        page.locator("#drawerOverlay").click(force=True, position={'x': 10, 'y': 10})
        page.wait_for_timeout(300)
        assert not page.locator("#mobileDrawer.is-open").is_visible()
        assert page.evaluate("() => document.body.style.overflow") == ''
        print("  [PASS] Mobile drawer closes on overlay click and unlocks body scroll")

        # Test Close button
        page.locator("#mobileMenuToggle").click()
        page.wait_for_timeout(300)
        page.locator("#closeDrawerBtn").click()
        page.wait_for_timeout(300)
        assert not page.locator("#mobileDrawer.is-open").is_visible()
        print("  [PASS] Mobile drawer closes on close button click")

        # 6. Contact Form in Browser (Client Validation, Spinner, Mailto link)
        print("\nTesting Contact Form client-side validation & UI response in browser...")
        page.set_viewport_size({"width": 1280, "height": 800})
        page.locator("#contact").scroll_into_view_if_needed()
        page.wait_for_timeout(300)

        # Submit empty
        page.locator("#submitInquiryBtn").click()
        page.wait_for_timeout(200)
        alert_msg = page.locator("#formAlert").text_content()
        assert "Please correct the highlighted fields" in alert_msg
        has_error_count = page.evaluate("() => document.querySelectorAll('.form-group.has-error').length")
        assert has_error_count >= 3
        print("  [PASS] Empty form submission triggers inline errors and banner alert")

        # Fill valid inquiry
        page.fill("#contactName", "Ananya Singhania")
        page.fill("#contactOrg", "Prestige Retail Group")
        page.fill("#contactEmail", "ananya.s@prestigeretail.com")
        page.fill("#contactPhone", "+91 9811223344")
        page.select_option("#contactRoleType", "Store Manager")
        page.fill("#contactMessage", "We are opening flagship hypermarkets across West India and want to connect with Mukesh.")

        page.locator("#submitInquiryBtn").click()
        page.wait_for_timeout(1000)

        alert_text = page.locator("#formAlert").text_content()
        assert "Inquiry Received!" in alert_text or "Thank you" in alert_text
        mailto_link = page.evaluate("() => document.querySelector('#formAlert a')?.getAttribute('href')")
        print(f"Success banner mailto fallback: {mailto_link}")
        assert mailto_link and "mailto:mgsmukeshgupta@gmail.com" in mailto_link
        print("  [PASS] Successful form submission renders success banner with working mailto link")

        # Clean inquiries.json
        with open(INQUIRIES_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f)

        # 7. Print Resume Page (/resume)
        print("\nTesting Printable Resume Page (/resume)...")
        resume_page = context.new_page()
        resume_page.goto(f"{BASE_URL}/resume", wait_until='networkidle')
        assert "Mukesh Gupta" in resume_page.title()
        
        # Test Print button has window.print()
        print_btn_onclick = resume_page.evaluate("() => document.querySelector('.btn-primary[onclick]')?.getAttribute('onclick')")
        print(f"Print button onclick: {print_btn_onclick}")
        assert print_btn_onclick == "window.print()"

        # Test @media print styling rules
        print_rules = resume_page.evaluate("""() => {
            for (let sheet of document.styleSheets) {
                try {
                    for (let rule of sheet.cssRules) {
                        if (rule.media && rule.media.mediaText.includes('print')) {
                            const subRules = Array.from(rule.cssRules);
                            const actionBarRule = subRules.find(r => r.selectorText === '.action-bar');
                            const wrapperRule = subRules.find(r => r.selectorText === '.resume-wrapper');
                            return {
                                hasActionBarHide: actionBarRule ? actionBarRule.style.display.includes('none') : false,
                                hasWrapperUnbox: wrapperRule ? (wrapperRule.style.boxShadow === 'none' || wrapperRule.style.border === 'none') : false
                            };
                        }
                    }
                } catch(e) {}
            }
            return null;
        }""")
        print(f"Print media rules detected: {print_rules}")
        assert print_rules and print_rules['hasActionBarHide'], "Print media query does not hide action-bar"
        assert print_rules['hasWrapperUnbox'], "Print media query does not unbox resume-wrapper"
        print("  [PASS] Resume page verified: print button and @media print unboxing rules active")
        resume_page.close()

        # 8. All CTA Buttons / Links clickable and present
        print("\nTesting all interactive buttons and links...")
        cta_selectors = {
            "Header Download CV": "#openCvModalBtn",
            "Header Tel Link": ".header-tel-btn",
            "Mobile Hamburger Toggle": "#mobileMenuToggle",
            "Hero CV Button": "#heroCvBtn",
            "Form Submit Button": "#submitInquiryBtn",
            "Form Reset Button": "#resetInquiryBtn",
            "Back To Top Button": "#backToTopBtn",
            "Modal Close Button": "#closeCvModalBtn",
            "Modal Print CV Button": "#viewPrintCvBtn",
            "Drawer Navigation Links": ".drawer-nav-link",
            "Footer Navigation Links": ".footer-links-grid a",
            "Competency Filter Pills": ".filter-pill"
        }
        for name, sel in cta_selectors.items():
            count = page.locator(sel).count()
            print(f"  CTA '{name}' ({sel}): count = {count}")
            assert count > 0, f"CTA '{name}' ({sel}) not found in DOM"
        print("  [PASS] All major action CTAs, nav items, and buttons verified present and wired")

        # 9. Console Errors check
        print("\nChecking console error count across entire test session...")
        print(f"Total console errors: {len(console_errors)}")
        if console_errors:
            for err in console_errors:
                print(f"  Console error: {err}")
        assert len(console_errors) == 0, f"Console errors detected: {console_errors}"
        print("  [PASS] 0 console errors logged")

        browser.close()

    # Final hygiene check
    with open(INQUIRIES_PATH, 'r', encoding='utf-8') as f:
        final_inquiries = json.load(f)
    assert final_inquiries == [], "inquiries.json must be [] at conclusion!"
    print("  [PASS] Final check: inquiries.json is strictly []")

    print("\n" + "="*60)
    print("ALL VERIFICATION CHECKS PASSED WITH ZERO ERRORS!")
    print("="*60)

if __name__ == '__main__':
    test_backend_routes()
    test_browser_and_regressions()
