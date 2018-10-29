import facebook
import json

from flask import url_for, current_app

FIELDS_UNAVAILABLE = ['Title']

CONFIG_FIELDS = ["access_token", "page"]


def run(publishing, channel_config):
    """Publish the post on the selected page on Facebook"""
    json_data = json.loads(channel_config)
    acc_tok = json_data['access_token']
    page_id = json_data['page']
    page = get_page_from_id(acc_tok, page_id)
    if page is None:
        print("Invalid page ID")
        # TODO should add log here
        return
    try:
        graph = facebook.GraphAPI(access_token=page['access_token'])
        # check token validity
        debug = graph.debug_access_token(
            page['access_token'],
            current_app.config["FACEBOOK_APP_ID"],
            current_app.config["FACEBOOK_APP_SECRET"])
        if not debug['data']['is_valid']:
            print("Invalid Access-Token")
            # TODO should add log here
            return
        # publish post
        graph.put_object(
            parent_object="me",
            connection_name="feed",
            message=publishing.description,
            link=publishing.link_url)
    except facebook.GraphAPIError:
        print("GraphAPIError")
        # TODO should add log here
        return


def get_url_for_token(id_channel):
    """Return an URL to Facebook to get a valid access token."""
    app_id = current_app.config["FACEBOOK_APP_ID"]
    canvas_url = url_for('channels.callback_fb', _external=True)
    perms = ["manage_pages", "publish_pages"]
    graph = facebook.GraphAPI()
    url = graph.get_auth_url(app_id, canvas_url, perms)
    return url + "&state=" + str(id_channel)


def get_list_user_pages(acc_tok):
    """Return a list of dictionaries representing the Facebook pages of the user."""
    try:
        graph = facebook.GraphAPI(access_token=acc_tok)
        pages = graph.get_object('me/accounts')
        return pages['data']
    except facebook.GraphAPIError:
        return [{'id': '0', 'name': 'Unable to load user pages'}]


def get_page_from_id(acc_tok, page_id):
    """Return the dictionary corresponding to the page with id page_id"""
    if page_id == 0:
        return None
    try:
        graph = facebook.GraphAPI(access_token=acc_tok)
        pages = graph.get_object('me/accounts')
        for page in pages['data']:
            if page['id'] == page_id:
                return page
        return None
    except facebook.GraphAPIError:
        return None
