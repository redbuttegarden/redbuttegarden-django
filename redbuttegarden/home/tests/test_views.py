def test_robots_txt(client):
    """
    Test the robots.txt endpoint.
    """
    response = client.get('/robots.txt')
    assert response.status_code == 200
    # Assert that all user-agents are blocked from the admin interface
    assert 'User-agent: *\nDisallow: /admin/' in response.text