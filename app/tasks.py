import sys
import time
from rq import get_current_job
from app.models import Task, User, Review
from app import create_app, db


app = create_app()
app.app_context().push()


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()

def export_posts(user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_reviews = user.reviews.count()
        for review in user.reviews.order_by(Review.timestamp.asc()):
            data.append({'body': review.body,
                         'timestamp': review.timestamp.isoformat() + 'Z'})
            time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_posts)
    except:
        _set_task_progress(100)
        app.logger.error('Unhandled exception', exc_info = sys.exc_info())

