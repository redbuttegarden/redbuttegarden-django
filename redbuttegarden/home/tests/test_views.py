def test_robots_txt(client):
    """
    Test the robots.txt endpoint.
    """
    response = client.get('/robots.txt')
    assert response.status_code == 200
    # Assert that all user-agents are blocked from the admin interface
    assert 'User-agent: *\nDisallow: /admin/' in response.text


def test_offline_html_uses_default_cache_control(client):
    response = client.get("/offline/")

    assert response.status_code == 200
    assert response["Cache-Control"] == (
        "public, max-age=60, s-maxage=86400, must-revalidate, proxy-revalidate"
    )
