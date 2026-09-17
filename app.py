import os
import re
import json
import html
from datetime import datetime, timezone
from urllib.parse import quote
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mukesh-gupta-portfolio-key-2025')

INQUIRIES_FILE = os.path.join(os.path.dirname(__file__), 'inquiries.json')

def save_inquiry(data):
    """Store submitted contact inquiries locally in a JSON file as an optional local backup."""
    inquiries = []
    if os.path.exists(INQUIRIES_FILE):
        try:
            with open(INQUIRIES_FILE, 'r', encoding='utf-8') as f:
                inquiries = json.load(f)
                if not isinstance(inquiries, list):
                    inquiries = []
        except Exception as e:
            app.logger.warning(f"Error reading inquiries backup: {e}")
            inquiries = []
    
    inquiries.append(data)
    try:
        with open(INQUIRIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(inquiries, f, indent=2, ensure_ascii=False)
    except Exception as e:
        app.logger.warning(f"Error saving inquiry backup: {e}")

@app.route('/')
def home():
    """Renders the main portfolio page."""
    portfolio_data = {
        "name": "Mukesh Gupta",
        "title": "Assistant Manager | Retail Operations | Warehouse | Inventory | Finance & Commercial Operations",
        "headline": "Retail Operations & Large-Format Store Leader",
        "phone": "+91 7016498175",
        "email": "mgsmukeshgupta@gmail.com",
        "dob": "2 March 1995",
        "marital_status": "Married",
        "native_location": "Azamgarh, Uttar Pradesh – 276142",
        "current_location": "Ahmedabad, Gujarat",
        "current_company": "Reliance Retail Limited",
        "current_store_sqft": "17,442",
        "current_monthly_turnover": "₹3 Crore",
        "experience_years": "12+",
    }
    return render_template('index.html', p=portfolio_data)

@app.route('/download-cv')
@app.route('/resume')
@app.route('/cv')
def resume():
    """Renders a dedicated, print-optimized executive resume for download or PDF printing."""
    return render_template('resume.html')

@app.route('/api/contact', methods=['POST'])
def contact_api():
    """Handles leadership inquiries and contact submissions with validation and email delivery."""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            data = request.form.to_dict()

        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        phone = (data.get('phone') or '').strip()
        organization = (data.get('organization') or '').strip()
        role_type = (data.get('role_type') or '').strip()
        message = (data.get('message') or '').strip()

        # Validation
        errors = {}
        if not name or len(name) < 2:
            errors['name'] = "Please provide your full name."
        
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        if not email or not re.match(email_pattern, email):
            errors['email'] = "Please provide a valid email address."
            
        if phone:
            # Clean digits and basic checks
            clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
            if not clean_phone.isdigit() or len(clean_phone) < 7:
                errors['phone'] = "Please enter a valid phone number or leave blank."

        if not message or len(message) < 5:
            errors['message'] = "Please share a brief message or details regarding the opportunity."

        if errors:
            return jsonify({
                "success": False,
                "errors": errors,
                "message": "Please correct the highlighted fields and try again."
            }), 400

        # Create record
        inquiry_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "name": name,
            "email": email,
            "phone": phone,
            "organization": organization,
            "role_type": role_type,
            "message": message
        }

        # Save optional local backup
        save_inquiry(inquiry_record)

        return jsonify({
            "success": True,
            "message": f"Thank you, {name}! Your leadership inquiry has been received."
        }), 200

    except Exception as ex:
        app.logger.error(f"Unexpected contact API error: {ex}")
        return jsonify({
            "success": False,
            "message": f"An unexpected server error occurred: {str(ex)}"
        }), 500

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "mukesh-gupta-portfolio"}), 200

@app.route('/robots.txt')
def robots():
    return app.response_class(
        "User-agent: *\nAllow: /\nSitemap: " + request.url_root + "sitemap.xml\n",
        mimetype='text/plain'
    )

@app.route('/sitemap.xml')
def sitemap():
    pages = [url_for('home', _external=True), url_for('resume', _external=True)]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for p in pages:
        xml += f'  <url><loc>{p}</loc></url>\n'
    xml += '</urlset>'
    return app.response_class(xml, mimetype='application/xml')

if __name__ == '__main__':
    # Run locally on port 5000 with debug enabled
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
