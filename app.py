from flask import Flask, jsonify, render_template, request
# from flask_sqlalchemy import SQLAlchemy
from models import db, Channel, Video
from celery import Celery
import requests
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://balaji:balaji@localhost/test1'
#db = SQLAlchemy(app)
db.init_app(app)
app.config['CELERY_BROKER_URL'] = "redis://localhost:6379/0"
app.config['CELERY_RESULT_BACKEND'] = "redis://localhost:6379/0"


def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


celery = make_celery(app)
DEVELOPER_KEY = "AIzaSyDUVEW38BXvuMCRV0PzGTlYQk3J4tdcMfs"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

video_ids = [{'video_id': 'UHdgXkkVyl0'}, {'video_id': 'ORZltL9glEA'}, {'video_id': 'kJQP7kiw5Fk'}]


@app.route('/api/stats/videos')
def view_videos():
    videos = Video.get_all_videos()
    data = []
    for video in videos:
        final_content = {
            'videoId': video.video_id,
            'channelId': video.channel_id,
            'commentCount': video.comment_count,
            'dislikeCount': video.dislike_count,
            'favoriteCount': video.favorite_count,
            'likeCount': video.like_count,
            'viewCount': video.view_count
        }
        data.append(final_content)

    return jsonify(data)


@app.route('/videolist')
def view_video_list():
    videos = Video.get_all_videos()
    return render_template('video_list.html', videos=videos)


@app.route('/video/<string:videoID>')
def view_specific_video(videoID):
    # video = Video.query.filter_by(id=videoID).first()
    video = Video.get_one_video(videoID)
    return render_template('video.html', video=video)


@app.route('/channellist')
def view_channel_list():
    channels = Channel.get_all_channels()
    return jsonify(channels)


@app.route('/channel/<string:channelID>')
def view_specific_channel(channelID):
    # channel = Channel.query.filter_by(id=channelID).first()
    channel = Channel.get_one_channel(channelID)
    return jsonify(channel)


CELERYBEAT_SCHEDULE = {
    'add-every-30-seconds': {
        'task': 'app.get_content',
        'schedule': 30.0,
        'args': ()
    },
}
app.config.timezone = 'UTC'


@celery.task
def get_content():

    youtube_id = 'ORZltL9glEA'
    r = requests.get(
        "https://www.googleapis.com/youtube/v3/videos?part=statistics&id={}%2C&key={}".format(youtube_id, DEVELOPER_KEY))
    r1 = requests.get("https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + youtube_id + "&key=" + DEVELOPER_KEY)
    data = json.loads(r.text)
    items = data['items'][0]
    data1 = json.loads(r1.text)
    items1 = data1['items'][0]
    channel_id = items1['snippet']['channelId']
    statistics = items['statistics']
    # result = Video(youtube_id, channel_id, comment_count, dislike_count, favorite_count, like_count, view_count)
    result = Video({'statistics': statistics, 'youtube_id': youtube_id, 'channel_id': channel_id})
    db.session.add(result)
    db.session.commit()
    print(result)

    # return jsonify({'statistics': statistics, 'youtube_id': youtube_id, 'channel_id': channel_id})
    # return {'statistics': statistics, 'youtube_id': youtube_id, 'channel_id': channel_id}
    return result


@app.route('/youtube', methods=['GET'])
def get_youtube_data():
    r = get_content.delay()
    print(r)
    return view_videos()


@app.route('/youtubeid', methods=['GET'])
def display():
    data = []
    count = 0
    for video in video_ids:
        youtube_id = video['video_id']
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/videos?part=statistics&id=" + youtube_id + "%2C&key="+DEVELOPER_KEY)
        values = json.loads(r.text)
        items = values['items'][0]
        content = items['statistics']
        final_content = {'video': content}
        # data[video] = content
        # data[count] = content
        data.append(final_content)
        count = count+1
    stats = json.dumps(data)
    statistics = json.loads(stats)
    # print(statistics)

    return jsonify({'statistics': statistics})


@app.route('/api/stats/<string:videoID>', methods=['GET'])
def display_stats(videoID):
    r = requests.get(
        "https://www.googleapis.com/youtube/v3/videos?part=statistics&id=" + videoID + "%2C&key="+DEVELOPER_KEY)
    data = json.loads(r.text)
    items = data['items'][0]
    statistics = items['statistics']

    return jsonify({'statistics': statistics})


@app.route('/channel', methods=['GET'])
def get_videos_from_channel_id():
    youtube_video_ids = []
    channel_id = get_channel_id_from_user_name()
    print(channel_id)
    r = requests.get("https://www.googleapis.com/youtube/v3/search?key=" + DEVELOPER_KEY + "&channelId=" + channel_id +
                     "&part=snippet,id&order=date&maxResults=20")
    data = json.loads(r.text)
    items = data['items']
    for item in items:
        id = item['id']
        try:
            video_id = id['videoId']
        except:
            video_id = id['playlistId']
        youtube_video_ids.append(video_id)

    return jsonify(youtube_video_ids)


def get_channel_id_from_user_name():
    user_name = 'wunderbarstudios'
    r = requests.get("https://www.googleapis.com/youtube/v3/channels?key=" + DEVELOPER_KEY + "&forUsername=" + user_name
                     + "&part=id")
    data = json.loads(r.text)
    items = data['items'][0]
    channel_id = items['id']

    return channel_id


@app.route('/channel/stats', methods=['GET'])
def get_stats_from_channel_id():
    channel_id = get_channel_id_from_user_name()
    r = requests.get(
        "https://www.googleapis.com/youtube/v3/channels?part=statistics&id=" + channel_id + "&key=" + DEVELOPER_KEY)
    data = json.loads(r.text)
    items = data['items'][0]
    statistics = items['statistics']

    return jsonify(statistics)


if __name__ == '__main__':
    app.run(debug=True, port=8080)
