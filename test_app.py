import pytest
import json
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'

def test_home_page_renders(client):
    response = client.get('/')
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert 'Mukesh Gupta' in content
    assert 'Retail Operations' in content
    assert '17,442' in content
    assert 'Reliance Retail Limited' in content
    assert '+91 7016498175' in content
    assert 'mgsmukeshgupta@gmail.com' in content

def test_resume_page_renders(client):
    response = client.get('/download-cv')
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert 'Mukesh Gupta' in content
    assert 'Executive Resume' in content or 'Resume & CV' in content

def test_contact_validation_missing_name(client):
    payload = {
        'name': '',
        'email': 'test@example.com',
        'message': 'Looking for a store manager'
    }
    response = client.post('/api/contact', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'name' in data['errors']

def test_contact_validation_invalid_email(client):
    payload = {
        'name': 'Test Recruiter',
        'email': 'invalid-email',
        'message': 'Looking for a store manager'
    }
    response = client.post('/api/contact', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'email' in data['errors']

def test_contact_validation_short_message(client):
    payload = {
        'name': 'Test Recruiter',
        'email': 'recruiter@company.com',
        'message': 'Hi'
    }
    response = client.post('/api/contact', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'message' in data['errors']

def test_contact_successful_submission(client, monkeypatch):
    monkeypatch.setattr('app.save_inquiry', lambda data: None)
    monkeypatch.setattr('app.send_inquiry_email', lambda data: True)
    payload = {
        'name': 'HR Director',
        'email': 'hr@retailenterprise.com',
        'phone': '+91 9876543210',
        'organization': 'Apex Retail Corp',
        'role_type': 'Store Manager',
        'message': 'We have an upcoming cluster manager mandate in Gujarat and would like to connect.'
    }
    response = client.post('/api/contact', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['email_sent'] is True
    assert 'Thank you' in data['message']
    assert 'delivered directly to Mukesh Gupta\'s inbox' in data['message']
    assert 'mailto_fallback' in data

def test_contact_email_failure_returns_503(client, monkeypatch):
    monkeypatch.setattr('app.save_inquiry', lambda data: None)
    def mock_send_fail(data):
        raise ConnectionRefusedError("Simulated SMTP network connection failure")
    monkeypatch.setattr('app.send_inquiry_email', mock_send_fail)

    payload = {
        'name': 'HR Director',
        'email': 'hr@retailenterprise.com',
        'phone': '+91 9876543210',
        'organization': 'Apex Retail Corp',
        'role_type': 'Store Manager',
        'message': 'We have an upcoming cluster manager mandate in Gujarat and would like to connect.'
    }
    response = client.post('/api/contact', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 503
    data = json.loads(response.data)
    assert data['success'] is False
    assert data['email_sent'] is False
    assert 'could not deliver your message' in data['message']
    assert 'mailto_fallback' in data
    assert 'mailto:mgsmukeshgupta@gmail.com' in data['mailto_fallback']

def test_contact_missing_smtp_credentials_fails_honestly(client, monkeypatch):
    # Ensure SMTP env vars are unset
    monkeypatch.delenv('SMTP_HOST', raising=False)
    monkeypatch.delenv('SMTP_USERNAME', raising=False)
    monkeypatch.delenv('SMTP_PASSWORD', raising=False)
    monkeypatch.setattr('app.save_inquiry', lambda data: None)

    payload = {
        'name': 'Talent Acquisition',
        'email': 'ta@retailgroup.in',
        'phone': '+91 9811223344',
        'message': 'Looking for an experienced cluster store leader.'
    }
    response = client.post('/api/contact', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 503
    data = json.loads(response.data)
    assert data['success'] is False
    assert data['email_sent'] is False
    assert 'could not deliver your message' in data['message']
    assert 'mailto_fallback' in data

def test_send_inquiry_email_structure_and_reply_to(monkeypatch):
    import app as app_module
    from unittest.mock import MagicMock

    monkeypatch.setenv('SMTP_HOST', 'smtp.example.com')
    monkeypatch.setenv('SMTP_PORT', '587')
    monkeypatch.setenv('SMTP_USERNAME', 'sender@example.com')
    monkeypatch.setenv('SMTP_PASSWORD', 'secret123')
    monkeypatch.setenv('OWNER_EMAIL', 'mgsmukeshgupta@gmail.com')

    sent_messages = []
    mock_smtp_instance = MagicMock()
    def mock_send_message(msg):
        sent_messages.append(msg)
    mock_smtp_instance.send_message = mock_send_message
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance

    monkeypatch.setattr('smtplib.SMTP', lambda host, port, timeout=20: mock_smtp_instance)

    test_data = {
        'timestamp': '2026-09-17T18:00:00Z',
        'name': 'Rajesh Sharma',
        'email': 'rajesh@company.com',
        'phone': '+91 9876543210',
        'organization': 'Apex Retail Corp',
        'role_type': 'Retail Operations Manager',
        'message': 'We are hiring a Cluster Operations Lead in Gujarat.'
    }

    app_module.send_inquiry_email(test_data)

    assert len(sent_messages) == 1
    msg = sent_messages[0]
    assert msg['To'] == 'mgsmukeshgupta@gmail.com'
    assert 'sender@example.com' in msg['From']
    assert 'rajesh@company.com' in msg['Reply-To']
    assert 'Rajesh Sharma' in msg['Reply-To']
    assert 'Leadership Inquiry' in msg['Subject']
    assert 'Retail Operations Manager' in msg['Subject']

    # Check payload parts
    payloads = [p.get_payload(decode=True).decode('utf-8') for p in msg.get_payload()]
    combined_body = " ".join(payloads)
    assert 'Rajesh Sharma' in combined_body
    assert 'Apex Retail Corp' in combined_body
    assert 'rajesh@company.com' in combined_body
    assert '+91 9876543210' in combined_body
    assert 'Retail Operations Manager' in combined_body
    assert 'Cluster Operations Lead in Gujarat' in combined_body
    assert '2026-09-17T18:00:00Z' in combined_body

def test_robots_endpoint(client):
    response = client.get('/robots.txt')
    assert response.status_code == 200
    assert 'User-agent: *' in response.data.decode('utf-8')
    assert 'sitemap.xml' in response.data.decode('utf-8')
    assert response.mimetype == 'text/plain'

def test_sitemap_endpoint(client):
    response = client.get('/sitemap.xml')
    assert response.status_code == 200
    assert '<urlset' in response.data.decode('utf-8')
    assert response.mimetype == 'application/xml'

def test_resume_alternate_routes(client):
    for route in ['/resume', '/cv']:
        res = client.get(route)
        assert res.status_code == 200
        assert 'Mukesh Gupta' in res.data.decode('utf-8')

