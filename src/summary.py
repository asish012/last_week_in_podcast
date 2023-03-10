import validators
import json
from flask import Blueprint, request
from flask import redirect, url_for
from flask.json import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from src.database import db, Summary, Activity
from src.summarizer import summarize_video, get_video_id
from src.constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT, HTTP_500_INTERNAL_SERVER_ERROR

summary = Blueprint("summary", __name__, url_prefix="/api/v1/summary")


@summary.post('/')
@jwt_required()
def save_summary():
    current_user = get_jwt_identity()

    video_id = request.get_json().get('video_id', '')
    title = request.get_json().get('title', '')
    context = request.get_json().get('context', '')

    yt_summary = Summary.query.filter_by(video_id=video_id).first()
    if yt_summary:
        update_user_activity(current_user, yt_summary.id)
        return jsonify_ytsummary(yt_summary), HTTP_200_OK

    try:
        summary_1, summary_2, transcript = summarize_video(video_id, title, context)

        yt_summary = Summary(video_id=video_id, summary_1=summary_1, summary_2=summary_2, transcript=transcript)
        db.session.add(yt_summary)
        db.session.commit()

        yt_summary = Summary.query.filter_by(video_id=video_id).first()
        update_user_activity(current_user, yt_summary.id)

        return jsonify_ytsummary(yt_summary), HTTP_201_CREATED
    except Exception as e:
        return jsonify({'message': str(e)}), HTTP_500_INTERNAL_SERVER_ERROR


@summary.get("/<string:video_id>")
@jwt_required()
def get_summary(video_id):
    yt_summary = Summary.query.filter_by(video_id=video_id).first()

    if not yt_summary:
        return jsonify({'message': 'Item not found'}), HTTP_404_NOT_FOUND

    return jsonify_ytsummary(yt_summary), HTTP_200_OK


@summary.delete("/<string:video_id>")
@jwt_required()
def delete_summary(video_id):
    current_user = get_jwt_identity()

    yt_summary = Summary.query.filter_by(video_id=video_id).first()

    if not yt_summary:
        return jsonify({'message': 'Item not found'}), HTTP_404_NOT_FOUND

    db.session.delete(yt_summary)
    db.session.commit()

    return jsonify({}), HTTP_204_NO_CONTENT


@summary.put('/<string:video_id>')
@summary.patch('/<string:video_id>')
@jwt_required()
def edit_summary(video_id):
    current_user = get_jwt_identity()

    yt_summary = Summary.query.filter_by(video_id=video_id).first()

    if not yt_summary:
        return jsonify({'message': 'Item not found'}), HTTP_404_NOT_FOUND

    video_id = request.get_json().get('video_id', '')
    summary_1 = request.get_json().get('summary_1', '')
    summary_2 = request.get_json().get('summary_2', '')
    transcript = request.get_json().get('transcript', '')

    yt_summary.summary_1 = summary_1
    yt_summary.summary_2 = summary_2
    yt_summary.transcript = transcript

    db.session.commit()

    return jsonify_ytsummary(yt_summary), HTTP_200_OK


# Functions

def jsonify_ytsummary(yt_summary):
    try:
        openai_summary = json.loads(yt_summary.summary_2)
        return jsonify({
            'video_id': yt_summary.video_id,
            'summary': openai_summary.get('summary', ''),
            'chapters': openai_summary.get('paragraphs', ''),
            'created_at': yt_summary.created_at,
            'updated_at': yt_summary.updated_at,
        })
    except Exception as e:
        raise Exception('Summary parsing error.', yt_summary)

def update_user_activity(current_user, summary_id):
    str_summary_id = str(summary_id)
    my_activity = Activity.query.filter_by(user_id=current_user).first()

    if not my_activity:
        my_activity = Activity(user_id=current_user, used_quota=1, summary_ids=str_summary_id)
        db.session.add(my_activity)
        db.session.commit()
    else:
        ids = my_activity.summary_ids.split(',')
        if str_summary_id not in ids:
            ids.append(str_summary_id)
            my_activity.summary_ids = ','.join(ids)
            my_activity.used_quota = my_activity.used_quota + 1
            db.session.commit()
