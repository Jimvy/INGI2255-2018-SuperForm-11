from flask import Blueprint, url_for, request, redirect, session, render_template

from superform.users import channels_available_for_user
from superform.utils import login_required, datetime_converter, str_converter, get_instance_from_module_path
from superform.models import db, Post, Publishing, Channel
from superform.publishings import create_a_publishing

posts_page = Blueprint('posts', __name__)


def create_a_post(form):
    user_id = session.get("user_id", "") if session.get("logged_in", False) else -1
    title_post = form.get('titlepost')
    descr_post = form.get('descriptionpost')
    link_post = form.get('linkurlpost')
    image_post = form.get('imagepost')
    date_from = datetime_converter(form.get('datefrompost'))
    date_until = datetime_converter(form.get('dateuntilpost'))
    p = Post(user_id=user_id, title=title_post, description=descr_post, link_url=link_post, image_url=image_post,
             date_from=date_from, date_until=date_until)
    db.session.add(p)
    db.session.commit()
    return p


def valid_date(form):
    try:
        datetime_converter(form.get('datefrompost'))
        datetime_converter(form.get('dateuntilpost'))
    except ValueError:
        return False
    return True


def get_data(form):
    user_id = session.get("user_id", "") if session.get("logged_in", False) else -1
    list_of_channels = channels_available_for_user(user_id)

    for elem in list_of_channels:
        m = elem.module
        clas = get_instance_from_module_path(m)
        unaivalable_fields = ','.join(clas.FIELDS_UNAVAILABLE)
        setattr(elem, "unavailablefields", unaivalable_fields)

    titles = {}
    descriptions = {}
    links = {}
    images = {}

    titles[0] = form.get('titlepost')
    descriptions[0] = form.get('descriptionpost')
    links[0] = form.get('linkurlpost')
    images[0] = form.get('imagepost')
    for elem in form:
        if elem.startswith("chan_option_"):
            def substr(elem):
                import re
                return re.sub('^chan\_option\_', '', elem)

            chn = Channel.query.get(substr(elem))
            chan = str(chn.name)
            titles[chn.id + 1] = form.get(chan + '_titlepost') if (form.get(chan + '_titlepost') is not None) else form.get('titlepost')
            descriptions[chn.id + 1] = form.get(chan + '_descriptionpost') if form.get(
                chan + '_descriptionpost') is not None else form.get('descriptionpost')
            links[chn.id + 1] = form.get(chan + '_linkurlpost') if form.get(chan + '_linkurlpost') is not None else form.get('linkurlpost')
            images[chn.id + 1] = form.get(chan + '_imagepost') if form.get(chan + '_imagepost') is not None else form.get('imagepost')

    return [list_of_channels, titles, descriptions, links, images]


@posts_page.route('/new', methods=['GET', 'POST'])
@login_required()
def new_post():
    user_id = session.get("user_id", "") if session.get("logged_in", False) else -1
    list_of_channels = channels_available_for_user(user_id)
    for elem in list_of_channels:
        m = elem.module
        clas = get_instance_from_module_path(m)
        unaivalable_fields = ','.join(clas.FIELDS_UNAVAILABLE)
        setattr(elem, "unavailablefields", unaivalable_fields)

    if request.method == "GET":
        return render_template('new.html', l_chan=list_of_channels)
    else:
        create_a_post(request.form)
        return redirect(url_for('index'))


@posts_page.route('/publish', methods=['POST'])
@login_required()
def publish_from_new_post():
    # First create the post
    if valid_date(request.form):
        p = create_a_post(request.form)
    else:
        values = get_data(request.form)
        return render_template('new.html', l_chan=values[0], not_valid_date=True, titles=values[1], descriptions=values[2], links=values[3], images=values[4])
    # then treat the publish part
    if request.method == "POST":
        for elem in request.form:
            if elem.startswith("chan_option_"):
                def substr(elem):
                    import re
                    return re.sub('^chan\_option\_', '', elem)

                c = Channel.query.get(substr(elem))
                # for each selected channel options
                # create the publication
                pub = create_a_publishing(p, c, request.form)

    db.session.commit()
    return redirect(url_for('index'))


@posts_page.route('/records')
@login_required()
def records():
    posts = db.session.query(Post).filter(Post.user_id == session.get("user_id", ""))
    records = [(p) for p in posts if p.is_a_record()]
    return render_template('records.html', records=records)
