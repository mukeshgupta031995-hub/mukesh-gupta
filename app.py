import os
import re
import json
import html
import ssl
import smtplib
from datetime import datetime, timezone
from urllib.parse import quote
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
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

def get_smtp_config():
    """Retrieve SMTP configuration from environment variables."""
    host = os.environ.get('SMTP_HOST', '').strip()
    port_str = os.environ.get('SMTP_PORT', '587').strip()
    try:
        port = int(port_str) if port_str else 587
    except ValueError:
        port = 587
    username = os.environ.get('SMTP_USERNAME', '').strip()
    password = os.environ.get('SMTP_PASSWORD', '').strip()
    owner_email = os.environ.get('OWNER_EMAIL', 'mgsmukeshgupta@gmail.com').strip() or 'mgsmukeshgupta@gmail.com'
    return host, port, username, password, owner_email

def send_inquiry_email(data):
    """
    Sends the inquiry details to the portfolio owner via secure SMTP/TLS.
    Raises RuntimeError if credentials are missing, or smtplib exceptions on network/auth failure.
    """
    host, port, username, password, owner_email = get_smtp_config()

    if not host or not username or not password:
        raise RuntimeError("SMTP configuration is missing. Set SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD.")

    name = data.get('name', '').strip() or 'Inquirer'
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip() or 'Not provided'
    organization = data.get('organization', '').strip() or 'Not specified'
    role_type = data.get('role_type', '').strip() or 'General Leadership Inquiry'
    message = data.get('message', '').strip()
    timestamp = data.get('timestamp', '')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Leadership Inquiry from {name} - {role_type}"
    msg['From'] = formataddr(("Mukesh Gupta Portfolio", username))
    msg['To'] = owner_email
    if email:
        msg['Reply-To'] = formataddr((name, email))

    text_body = f"""New Leadership Inquiry Received

Submission Details:
-------------------------------------------
Timestamp (UTC): {timestamp}
Name / Title:    {name}
Organization:    {organization}
Email:           {email}
Phone / WhatsApp:{phone}
Role Type:       {role_type}

Opportunity Details / Message:
-------------------------------------------
{message}

-------------------------------------------
Reply directly to this email to respond to {name} ({email}).
Sent via Portfolio Contact Form.
"""

    safe_name = html.escape(name)
    safe_org = html.escape(organization)
    safe_email = html.escape(email)
    safe_phone = html.escape(phone)
    safe_role = html.escape(role_type)
    safe_message = html.escape(message).replace('\n', '<br>')
    safe_timestamp = html.escape(timestamp)

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b1329; margin: 0; padding: 24px; color: #1e293b; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; }}
    .header {{ background: linear-gradient(135deg, #0b1329 0%, #1a2744 100%); color: #ffffff; padding: 24px; }}
    .header h2 {{ margin: 0; font-size: 20px; font-weight: 700; color: #d4af37; }}
    .header p {{ margin: 6px 0 0; font-size: 13px; color: #94a3b8; }}
    .content {{ padding: 24px; }}
    .field {{ margin-bottom: 16px; }}
    .field-label {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: #64748b; margin-bottom: 4px; }}
    .field-value {{ font-size: 15px; color: #0f172a; font-weight: 500; }}
    .message-card {{ background: #f8fafc; border-left: 4px solid #d4af37; border-radius: 4px; padding: 16px; margin-top: 8px; font-size: 15px; line-height: 1.6; color: #1e293b; }}
    .action-row {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0; text-align: center; }}
    .reply-btn {{ display: inline-block; background: #0b1329; color: #ffffff !important; padding: 10px 22px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px; }}
    .footer {{ padding: 16px 24px; background: #f1f5f9; font-size: 12px; color: #64748b; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2>New Leadership Inquiry</h2>
      <p>Received via portfolio contact form on {safe_timestamp} UTC</p>
    </div>
    <div class="content">
      <div class="field">
        <div class="field-label">Candidate / Sender Name</div>
        <div class="field-value"><strong>{safe_name}</strong></div>
      </div>
      <div class="field">
        <div class="field-label">Organization / Company</div>
        <div class="field-value">{safe_org}</div>
      </div>
      <div class="field">
        <div class="field-label">Email Address</div>
        <div class="field-value"><a href="mailto:{safe_email}">{safe_email}</a></div>
      </div>
      <div class="field">
        <div class="field-label">Phone / WhatsApp</div>
        <div class="field-value">{safe_phone}</div>
      </div>
      <div class="field">
        <div class="field-label">Opportunity / Role Type</div>
        <div class="field-value">{safe_role}</div>
      </div>
      <div class="field">
        <div class="field-label">Opportunity Details / Message</div>
        <div class="message-card">{safe_message}</div>
      </div>
      <div class="action-row">
        <a href="mailto:{safe_email}" class="reply-btn">Reply to {safe_name}</a>
      </div>
    </div>
    <div class="footer">
      You can directly hit "Reply" in your email client to respond to {safe_name} ({safe_email}).
    </div>
  </div>
</body>
</html>
"""

    msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    context = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as server:
            server.login(username, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(username, password)
            server.send_message(msg)

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

        # 1. Save local backup (optional, does not block request if filesystem is read-only)
        save_inquiry(inquiry_record)

        # 2. Build pre-filled mailto fallback URL
        _, _, _, _, owner_email = get_smtp_config()
        subject_str = f"Leadership Inquiry from {name}"
        mailto_fallback = f"mailto:{owner_email}?subject={quote(subject_str)}&body={quote(message)}"

        # 3. Deliver via secure SMTP/TLS
        try:
            send_inquiry_email(inquiry_record)
        except Exception as email_err:
            app.logger.error(f"Email delivery failed: {email_err}")
            return jsonify({
                "success": False,
                "email_sent": False,
                "message": "We could not deliver your message right now due to an email server issue. Please use the direct email link below.",
                "mailto_fallback": mailto_fallback
            }), 503

        # 4. Confirmation returned ONLY upon successful email delivery
        return jsonify({
            "success": True,
            "email_sent": True,
            "message": f"Thank you, {name}! Your inquiry has been delivered directly to Mukesh Gupta's inbox. You will receive a response shortly.",
            "mailto_fallback": mailto_fallback
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
