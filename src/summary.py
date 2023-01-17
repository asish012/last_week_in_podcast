import validators
from flask import Blueprint, request
from flask import redirect, url_for
from flask.json import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from src.database import Summary, db
from src.summarizer import summarize_with_openai, get_video_id
from src.constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

summary = Blueprint("summary", __name__, url_prefix="/api/v1/summary")


@summary.post('/')
@jwt_required()
def save_summary():
    current_user = get_jwt_identity()

    url = request.get_json().get('url', '')

    if not validators.url(url):
        return jsonify({
            'error': 'Invalid url'
        }), HTTP_400_BAD_REQUEST

    video_id = get_video_id(url)
    if Summary.query.filter_by(video_id=video_id).first():
        return jsonify({
            'error': 'Video summary already exists'
        }), HTTP_409_CONFLICT

    url, video_id, summary_1, summary_2, transcript = summarize_with_openai(url)

    yt_summary = Summary(url=url, video_id=video_id, summary_1=summary_1, summary_2=summary_2, transcript=transcript, user_id=current_user)
    db.session.add(yt_summary)
    db.session.commit()

    return jsonify({
        'id': yt_summary.id,
        'url': yt_summary.url,
        'video_id': yt_summary.video_id,
        'summary_1': yt_summary.summary_1,
        'summary_2': yt_summary.summary_2,
        'transcript': yt_summary.transcript,
        'user_id': yt_summary.user_id,
        'created_at': yt_summary.created_at,
        'updated_at': yt_summary.updated_at,
    }), HTTP_201_CREATED


@summary.get("/<string:video_id>")
@jwt_required()
def get_summary(video_id):
    current_user = get_jwt_identity()

    yt_summary = Summary.query.filter_by(user_id=current_user, video_id=video_id).first()

    if not yt_summary:
        return jsonify({'message': 'Item not found'}), HTTP_404_NOT_FOUND

    return jsonify({
        'id': yt_summary.id,
        'url': yt_summary.url,
        'video_id': yt_summary.video_id,
        'summary_1': yt_summary.summary_1,
        'summary_2': yt_summary.summary_2,
        'transcript': yt_summary.transcript,
        'user_id': yt_summary.user_id,
        'created_at': yt_summary.created_at,
        'updated_at': yt_summary.updated_at,
    }), HTTP_200_OK


@summary.delete("/<string:video_id>")
@jwt_required()
def delete_summary(video_id):
    current_user = get_jwt_identity()

    yt_summary = Summary.query.filter_by(user_id=current_user, video_id=video_id).first()

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

    yt_summary = Summary.query.filter_by(user_id=current_user, video_id=video_id).first()

    if not yt_summary:
        return jsonify({'message': 'Item not found'}), HTTP_404_NOT_FOUND

    url = request.get_json().get('url', '')
    video_id = request.get_json().get('video_id', '')
    summary_1 = request.get_json().get('summary_1', '')
    summary_2 = request.get_json().get('summary_2', '')
    transcript = request.get_json().get('transcript', '')

    if not validators.url(url):
        return jsonify({
            'error': 'Invalid url'
        }), HTTP_400_BAD_REQUEST

    yt_summary.url = url
    yt_summary.summary_1 = summary_1
    yt_summary.summary_2 = summary_2
    yt_summary.transcript = transcript

    db.session.commit()

    return jsonify({
        'id': yt_summary.id,
        'url': yt_summary.url,
        'video_id': yt_summary.video_id,
        'summary_1': yt_summary.summary_1,
        'summary_2': yt_summary.summary_2,
        'transcript': yt_summary.transcript,
        'user_id': yt_summary.user_id,
        'created_at': yt_summary.created_at,
        'updated_at': yt_summary.updated_at,
    }), HTTP_200_OK
