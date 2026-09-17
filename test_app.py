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
    assert 'Thank you' in data['message']


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

