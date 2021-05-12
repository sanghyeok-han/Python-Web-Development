from datetime import datetime
from healthton import db, login_manager
from flask_login import UserMixin
import pytz

## 콘솔 작업

# db 생성 코드

# from hackathon import db
# db.create_all()

# db 내보내기 코드

# import pandas as pd
# from hackathon import db
# from hackathon.models import User, Post, Notice
# import os.path
# from sqlalchemy import create_engine
# basedir = os.path.abspath(os.path.dirname(__file__))
# sql_engine = create_engine(os.path.join('sqlite:///' + os.path.join(basedir, "hackathon\\site.db")), echo=False)
# results = pd.read_sql_query('select * from users', sql_engine)
# results.to_csv(os.path.join(basedir, 'users.csv'), encoding="utf-8-sig", index=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def get_korean_datetime():
    return datetime.now(pytz.timezone("Asia/Seoul"))


gathering_contracts = db.Table("gathering_contracts", db.metadata,
                               db.Column("id", db.String(20), db.ForeignKey("users.id")),
                               db.Column("gathering_id", db.Integer, db.ForeignKey("gatherings.gathering_id"))
                               )

attending_contracts = db.Table("attending_contracts", db.metadata,
                               db.Column("trainee_id", db.String(20), db.ForeignKey("trainees.trainee_id")),
                               db.Column("lecture_id", db.Integer, db.ForeignKey("lectures.lecture_id"))
                               )


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.String(20), primary_key=True)
    user_name = db.Column(db.String(10), unique=True, nullable=False)
    user_email = db.Column(db.String(120), unique=True, nullable=False)
    user_password = db.Column(db.String(60), nullable=False)
    user_address = db.Column(db.String(50), nullable=True)
    user_profile_content = db.Column(db.Text, nullable=False, default="")
    user_profile_image = db.Column(db.String(20), nullable=False, default='default.jpg')
    user_signed_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_signed_local_datetime = db.Column(db.DateTime, nullable=False, default=get_korean_datetime)
    user_gender = db.Column(db.String(2), nullable=True)
    user_type = db.Column(db.String, nullable=False)

    user_posts = db.relationship("Post", backref="user", lazy=True, primaryjoin="User.id == Post.post_writer_id")
    user_post_comments = db.relationship("PostComment", backref="user", lazy=True,
                                         primaryjoin="User.id == PostComment.post_comment_writer_id")
    user_notices = db.relationship("Notice", backref="user", lazy=True,
                                   primaryjoin="User.id == Notice.notice_writer_id")
    user_participating_gatherings = db.relationship("Gathering", secondary=gathering_contracts,
                                                    backref=db.backref("gathering_participants", lazy="dynamic"))

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }


class Trainer(User):
    __tablename__ = "trainers"
    trainer_id = db.Column(db.String(20), db.ForeignKey("users.id"), primary_key=True)
    trainer_major = db.Column(db.String(30), nullable=False, default="미정")
    assigned_gym_gym_manager_id = db.Column(db.String(20), db.ForeignKey("gym_managers.gym_manager_id"), nullable=True)

    lectures = db.relationship("TeachingContract", back_populates="trainer")

    __mapper_args__ = {
        "polymorphic_identity": "trainer"
    }


# user -> trainee 또는 제거 가능
class Trainee(User):
    __tablename__ = "trainees"
    trainee_id = db.Column(db.String(20), db.ForeignKey("users.id"), primary_key=True)
    trainee_is_deposited = db.Column(db.Boolean, nullable=False, default=False)

    lecture_attendances = db.relationship("Attendance", backref="trainee", lazy=True,
                                          primaryjoin="Trainee.trainee_id == Attendance.attendance_trainee_id")
    user_attending_lectures = db.relationship("Lecture", secondary=attending_contracts,
                                              backref=db.backref("lecture_attendees", lazy="dynamic"))

    __mapper_args__ = {
        "polymorphic_identity": "trainee"
    }


class GymManager(User):
    __tablename__ = "gym_managers"
    gym_manager_id = db.Column(db.String(20), db.ForeignKey("users.id"), primary_key=True)
    business_license_number = db.Column(db.String(12), nullable=False, default="NA")

    __mapper_args__ = {
        "polymorphic_identity": "gym_manager"
    }

    assigned_trainers = db.relationship("Trainer", backref="gym_manager", lazy=True,
                                        primaryjoin="GymManager.gym_manager_id == "
                                                    "Trainer.assigned_gym_gym_manager_id")


class Operator(User):
    __tablename__ = "operators"
    operator_id = db.Column(db.String(20), db.ForeignKey("users.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "operator"
    }

# laeture_days를 lecture_local_days로 변경 가능함
class Lecture(db.Model):
    __tablename__ = "lectures"
    lecture_id = db.Column(db.Integer, primary_key=True)
    lecture_type = db.Column(db.String(30), nullable=False)
    lecture_title = db.Column(db.String(100), nullable=False)
    lecture_content = db.Column(db.Text, nullable=False)
    lecture_thumbnail = db.Column(db.String(20), nullable=False, default="default.jpg")
    lecture_uploaded_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lecture_uploaded_local_datetime = db.Column(db.DateTime, nullable=False, default=get_korean_datetime)
    lecture_open_local_date = db.Column(db.DateTime, nullable=False)
    lecture_close_local_date = db.Column(db.DateTime, nullable=False)
    lecture_start_local_time = db.Column(db.DateTime, nullable=False)
    lecture_end_local_time = db.Column(db.DateTime, nullable=False)
    lecture_max_attendees_num = db.Column(db.Integer, nullable=True)
    lecture_current_attendees_num = db.Column(db.Integer, nullable=False, default=0)

    trainers = db.relationship("TeachingContract", back_populates="lecture")
    lecture_days = db.relationship("LectureDay", backref="lecture", lazy=True,
                                   primaryjoin="Lecture.lecture_id == LectureDay.lecture_day_lecture_id")
    lecture_attendances = db.relationship("Attendance", backref="lecture", lazy=True,
                                          primaryjoin="Lecture.lecture_id == Attendance.attendance_lecture_id")


class LectureDay(db.Model):
    __tablename__ = "lecture_days"
    lecture_day_id = db.Column(db.Integer, primary_key=True)
    lecture_day_lecture_id = db.Column(db.Integer, db.ForeignKey("lectures.lecture_id"), nullable=False)
    lecture_day_lecture_day = db.Column(db.String(3), nullable=False)


class TeachingContract(db.Model):
    __tablename__ = "teaching_contracts"
    trainer_id = db.Column(db.String(20), db.ForeignKey("trainers.trainer_id"), primary_key=True)
    lecture_id = db.Column(db.Integer, db.ForeignKey("lectures.lecture_id"), primary_key=True)
    participation_type = db.Column(db.String(10), nullable=False)

    trainer = db.relationship("Trainer", back_populates="lectures")
    lecture = db.relationship("Lecture", back_populates="trainers")


class Attendance(db.Model):
    __tablename__ = "attendances"
    attendance_id = db.Column(db.Integer, primary_key=True)
    attendance_trainee_id = db.Column(db.String(20), db.ForeignKey("trainees.trainee_id"), nullable=False)
    attendance_lecture_id = db.Column(db.Integer, db.ForeignKey("lectures.lecture_id"), nullable=False)
    attendance_lecture_local_date = db.Column(db.DateTime, nullable=False)
    attendance_lecture_local_day = db.Column(db.String(3), nullable=False)
    attendance_has_attended = db.Column(db.Boolean, nullable=False, default=False)


class Gathering(db.Model):
    __tablename__ = "gatherings"
    gathering_id = db.Column(db.Integer, primary_key=True)
    gathering_type = db.Column(db.String(20), nullable=False)
    gathering_title = db.Column(db.String(100), nullable=False)
    gathering_content = db.Column(db.Text, nullable=False)
    gathering_thumbnail = db.Column(db.String(20), nullable=False, default="default.jpg")
    gathering_address = db.Column(db.String(50), nullable=False)
    gathering_gym_manager_id = db.Column(db.String(20), db.ForeignKey("gym_managers.gym_manager_id"), nullable=False)
    gathering_uploaded_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    gathering_uploaded_local_datetime = db.Column(db.DateTime, nullable=False, default=get_korean_datetime)
    gathering_start_local_datetime = db.Column(db.DateTime, nullable=True)
    gathering_end_local_datetime = db.Column(db.DateTime, nullable=True)
    gathering_max_participants_num = db.Column(db.Integer, nullable=True)
    gathering_current_participants_num = db.Column(db.Integer, nullable=False, default=0)


class Notice(db.Model):
    __tablename__ = "notices"
    notice_id = db.Column(db.Integer, primary_key=True)
    notice_writer_id = db.Column(db.String(20), db.ForeignKey("users.id"), nullable=False)
    notice_title = db.Column(db.String(100), nullable=False)
    notice_content = db.Column(db.Text, nullable=False)
    notice_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notice_local_datetime = db.Column(db.DateTime, nullable=False, default=get_korean_datetime)
    notice_image = db.Column(db.String(20), nullable=False, default="no_image.jpg")
    notice_page_view = db.Column(db.Integer, nullable=False, default=0)


class Post(db.Model):
    __tablename__ = "posts"
    post_id = db.Column(db.Integer, primary_key=True)
    post_writer_id = db.Column(db.String(20), db.ForeignKey("users.id"), nullable=False)
    post_title = db.Column(db.String(100), nullable=False)
    post_content = db.Column(db.Text, nullable=False)
    post_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    post_local_datetime = db.Column(db.DateTime, nullable=False, default=get_korean_datetime)
    post_image = db.Column(db.String(20), nullable=False, default="no_image.jpg")
    post_page_view = db.Column(db.Integer, nullable=False, default=0)


    post_comments = db.relationship("PostComment", backref="post", lazy=True,
                                    primaryjoin="Post.post_id == PostComment.post_comment_post_id")


class PostComment(db.Model):
    __tablename__ = "post_comments"
    post_comment_id = db.Column(db.Integer, primary_key=True)
    post_comment_writer_id = db.Column(db.String(20), db.ForeignKey("users.id"), nullable=False)
    post_comment_post_id = db.Column(db.Integer, db.ForeignKey("posts.post_id"), nullable=False)
    post_comment_content = db.Column(db.Text, nullable=False)
    post_comment_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    post_comment_local_datetime = db.Column(db.DateTime, nullable=False, default=get_korean_datetime)
