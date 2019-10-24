from flask import render_template, flash, redirect, url_for, request
from flask import current_app, jsonify
from datetime import datetime
from app import db
from app.main.forms import EditProfileForm, ReviewForm, MessageForm
from flask_login import current_user, login_required
from app.models import User, Review, Message, Notification
from app.main import bp



@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods = ['GET', 'POST'])
@bp.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    #TODO: this doesn't really go here, put it here for now.
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(body = form.review.data, author = current_user)
        db.session.add(review)
        db.session.commit()
        flash('Your review is now live!')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type = int)
    reviews = current_user.followed_reviews().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page = reviews.next_num) \
        if reviews.has_next else None
    prev_url = url_for('main.index', page = reviews.prev_num) \
        if reviews.has_prev else None
    return render_template('index.html', title = 'Home', form = form,
        reviews = reviews.items, next_url = next_url, prev_url = prev_url)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type = int)
    reviews = Review.query.order_by(Review.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page = reviews.next_num) \
        if reviews.has_next else None
    prev_url = url_for('main.explore', page = reviews.prev_num) \
        if reviews.has_prev else None
    return render_template('index.html', title = 'Explore', reviews = reviews.items,
        next_url = next_url, prev_url = prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username = username).first_or_404()
    page = request.args.get('page', 1, type = int)
    reviews = user.reviews.order_by(Review.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username = user.username, page = reviews.next_num) \
        if reviews.has_next else None
    prev_url = url_for('main.user', username = user.username, page = reviews.prev_num) \
        if reviews.has_prev else None
    return render_template('user.html', user = user, reviews = reviews.items,
        next_url = next_url, prev_url = prev_url)


@bp.route('/edit_profile', methods = ['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title = 'Edit Profile',
        form = form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('main.user', username = username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('main.user', username = username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('main.user', username = username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('main.user', username = username))

@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username = username).first_or_404()
    return render_template('user_popup.html', user = user)

@bp.route('/send_message/<recipient>', methods = ['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username = recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author = current_user, recipient = user,
                      body = form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('main.user', username = recipient))
    return render_template('send_message.html', title = 'Send Message',
                           form = form, recipient = recipient)

@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type = int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page = messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page = messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages = messages.items,
                            next_url = next_url, prev_url = prev_url)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type = float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


@bp.route('/export_reviews')
@login_required
def export_reviews():
    if current_user.get_task_in_progress('export_reviews'):
        flash('An export task is already in progress.')
    else:
        current_user.launch_task('export_reviews', 'Exporting reviews...')
        db.session.commit()
    return redirect(url_for('main.user', username = current_user.username))
