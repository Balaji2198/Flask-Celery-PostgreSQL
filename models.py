import flask_sqlalchemy

db = flask_sqlalchemy.SQLAlchemy()

# relation = db.Table('relation',
#     db.Column('videos_id', db.Integer, db.ForeignKey('video.id'), primary_key=True),
#     db.Column('channels_id', db.Integer, db.ForeignKey('channel.id'), primary_key=True)
# )


class Channel(db.Model):

    __tablename__ = 'channels'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(50))
    channel_id = db.Column(db.String(50))
    video_count = db.Column(db.Integer)
    view_count = db.Column(db.Integer)
    subscriber_count = db.Column(db.Integer)

    def __init__(self, data):
        self.user_name = data.get('user_name')
        self.channel_id = data.get('channel_id')
        self.video_count = data.get('video_count')
        self.view_count = data.get('view_count')
        self.subscriber_count = data.get('subscriber_count')

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all_channels():
        return Channel.query.all()

    @staticmethod
    def get_one_channel(id):
        return Channel.query.get(id)

    def __repr__(self):
        return '<id {}'.format(self.id)


class Video(db.Model):

    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    video_id = db.Column(db.String(50))
    channel_id = db.Column(db.String(50))
    comment_count = db.Column(db.Integer)
    dislike_count = db.Column(db.Integer)
    favorite_count = db.Column(db.Integer)
    like_count = db.Column(db.Integer)
    view_count = db.Column(db.Integer)

    def __init__(self, data):
        # print(data)
        statistics = data.get('statistics')
        self.video_id = data.get('youtube_id')
        self.channel_id = data.get('channel_id')
        self.comment_count = statistics.get('commentCount')
        self.dislike_count = statistics.get('dislikeCount')
        self.favorite_count = statistics.get('favoriteCount')
        self.like_count = statistics.get('likeCount')
        self.view_count = statistics.get('viewCount')

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all_videos():
        return Video.query.all()

    @staticmethod
    def get_one_video(video_id):
        return Video.query.get(video_id)

    def __repr__(self):
        return '<id {}'.format(self.id)
