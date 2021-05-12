import os
import secrets
import re
import pytz
from datetime import datetime, timedelta
from PIL import Image
import numpy as np
from flask import render_template, url_for, flash, redirect, request, abort
from healthton import app, db, bcrypt
from healthton.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, PostCommentForm,\
    NoticeForm, GatheringForm, ApplyingGatheringForm, RegionSearchForm, LectureForm,\
    ApplyingLectureForm
from healthton.models import User, Trainer, Trainee, GymManager, Operator, Post, PostComment, Notice, Gathering,\
    Lecture, LectureDay, TeachingContract, Attendance
from flask_login import login_user, current_user, logout_user, login_required

# from hackathon import db
# from hackathon.models import Lecture, Trainee, Attendance
# TeachingContract.query.all()
# db.session.delete(TeachingContract.query.all()[-1])
# db.session.commit()
# Attendance.query.all()


# 홈페이지
@app.route("/")
@app.route("/home")
def home():
    db.session.commit()
    notice = Notice.query.order_by(Notice.notice_datetime.desc()).first()
    if notice:
        notice_content_length = len(notice.notice_content)
    else:
        notice_content_length = 0
    posts = Post.query.order_by(Post.post_datetime.desc()).limit(10).all()
    gatherings = Gathering.query.order_by(Gathering.gathering_uploaded_local_datetime.desc()).limit(10).all()
    if notice is not None:
        notice_profile_image = url_for("static", filename="profile_pics/" + notice.user.user_profile_image)
    else:
        notice_profile_image = None

    return render_template('home.html', notice=notice, notice_content_length=notice_content_length,
                           posts=posts, gatherings=gatherings, notice_profile_image=notice_profile_image)


# 데이터 내보내기(운영자 기능)
@app.route("/export_data")
@login_required
def export_data():
    if current_user.user_type != "operator":
        abort(403)

    # import pandas as pd
    # from hackathon import db
    # from hackathon.models import User, Post, Notice
    # import os.path
    # from sqlalchemy import create_engine
    # basedir = os.path.abspath(os.path.dirname(__file__))
    # sql_engine = create_engine(os.path.join('sqlite:///' + os.path.join(basedir, "hackathon\\site.db")), echo=False)
    # results = pd.read_sql_query('select * from users', sql_engine)
    # results.to_csv(os.path.join(basedir, 'users.csv'), encoding="utf-8-sig", index=False)
    return render_template('export_data.html')


# 소개글 페이지
@app.route("/introduce")
def introduce():
    return render_template('introduce.html')


@app.route("/introduce_scrollspy")
def introduce_scrollspy():
    return render_template('introduce_scrollspy.html')


# 회원가입 페이지
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.user_password.data).decode('utf-8')

        # 운영자의 경우
        if form.user_id.data == "운영자" and form.user_name.data == "운영자":
            user = Operator(id=form.user_id.data, user_name=form.user_name.data, user_email=form.user_email.data,
                            user_password=hashed_password, user_gender=form.user_gender.data,
                            user_address=form.user_address.data, user_type="operator")
        elif form.user_type.data == "trainer":
            user = Trainer(id=form.user_id.data, user_name=form.user_name.data, user_email=form.user_email.data,
                           user_password=hashed_password, user_gender=form.user_gender.data,
                           user_address=form.user_address.data, user_type=form.user_type.data,
                           trainer_major=form.trainer_major.data)
        elif form.user_type.data == "gym_manager":
            if (len(form.business_license_number.data) != 12 or
                    "".join(re.findall(r"\d{3}-\d{2}-\d{5}", form.business_license_number.data)) !=
                    form.business_license_number.data):
                flash("사업자등록번호 형식이 일치하지 않습니다. (###-##-#####)", "danger")
                return redirect(url_for('register'))

            user = GymManager(id=form.user_id.data, user_name=form.user_name.data, user_email=form.user_email.data,
                              user_password=hashed_password, user_gender=form.user_gender.data,
                              user_address=form.user_address.data, user_type=form.user_type.data,
                              business_license_number=form.business_license_number.data)
        elif form.user_type.data == "trainee":
            user = Trainee(id=form.user_id.data, user_name=form.user_name.data, user_email=form.user_email.data,
                           user_password=hashed_password, user_gender=form.user_gender.data,
                           user_address=form.user_address.data, user_type=form.user_type.data)

        db.session.add(user)
        db.session.commit()
        flash("회원가입을 성공하셨습니다!", "success")
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


# 로그인 페이지
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=form.user_id.data).first()
        if user and bcrypt.check_password_hash(user.user_password, form.user_password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("로그인에 실패하였습니다. 아이디 또는 비밀번호를 다시 확인해 주세요!", "danger")
    return render_template("login.html", title="Login", form=form)


# 로그아웃 기능
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


# 프로필 사진을 저장 및 반환하는 함수
def save_and_return_image(form_image, final_folder_path, image_size=(200, 200)):
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(form_image.filename)
    image_file_name = random_hex + file_extension
    image_path = os.path.join(app.root_path, "static/" + final_folder_path, image_file_name)
    output_size = image_size
    image = Image.open(form_image)

    if image_size:
        image.thumbnail(output_size)

    image.save(image_path)
    return image_file_name


# 개인 계정 페이지
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.user_profile_image.data:
            profile_image = save_and_return_image(form.user_profile_image.data, "profile_pics", (200, 200))
            current_user.user_profile_image = profile_image
        current_user.user_profile_content = form.user_profile_content.data
        current_user.user_name = form.user_name.data
        current_user.user_email = form.user_email.data
        db.session.commit()
        flash("프로필 업데이트가 완료되었습니다!", "success")
        return redirect(url_for("account"))
    elif request.method == "GET":
        form.user_profile_content.data = current_user.user_profile_content
        form.user_name.data = current_user.user_name
        form.user_email.data = current_user.user_email
    profile_image = url_for("static", filename="profile_pics/" + current_user.user_profile_image)
    return render_template("account.html", title="Account", profile_image=profile_image, form=form)


# 게시판
@app.route("/bulletin_board")
def bulletin_board():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.post_datetime.desc()).paginate(page=page, per_page=20)
    return render_template("bulletin_board.html", title="Bulletin Board", posts=posts)


# 게시글 생성 페이지
@app.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        if form.post_image.data:
            post_image = save_and_return_image(form.post_image.data, "post_pics", (400, 400))
            post_image = url_for("static", filename="post_pics/" + post_image)
        else:
            post_image = "no_image"

        post = Post(post_title=form.post_title.data, post_content=form.post_content.data,
                    post_writer_id=current_user.id, post_image=post_image)
        db.session.add(post)
        db.session.commit()
        flash("게시글을 성공적으로 업로드하였습니다!", "success")
        return redirect(url_for("home"))
    return render_template("create_and_update_post.html", title="New Post", form=form,
                           legend="게시글 생성")


# 각각의 게시글
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def post(post_id):
    form = PostCommentForm()
    post = Post.query.get_or_404(post_id)
    page = request.args.get("page", 1, type=int)
    post_comments = PostComment.query.filter_by(post_comment_post_id=post_id)\
        .order_by(PostComment.post_comment_datetime.desc()).paginate(page=page, per_page=10)

    if form.validate_on_submit():
        post_comment = PostComment(post_comment_writer_id=current_user.id, post_comment_post_id=post_id,
                                   post_comment_content=form.post_comment_content.data)
        db.session.add(post_comment)
        db.session.commit()
        return redirect(url_for("post", post_id=post_id))

    post.post_page_view += 1
    db.session.commit()
    return render_template("post.html", title=post.post_title, form=form, post=post, post_comments=post_comments,
                           post_id=post_id, action="view")


# 게시글 업데이트 페이지
@app.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user != current_user and current_user.user_type != "operator":
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        if form.validate_on_submit():
            if form.post_image.data:
                post_image = save_and_return_image(form.post_image.data, "post_pics", (400, 400))
                post_image = url_for("static", filename="post_pics/" + post_image)
                post.post_image = post_image

        post.post_title = form.post_title.data
        post.post_content = form.post_content.data
        db.session.commit()
        flash("게시글 업데이트가 완료되었습니다!", "success")
        return redirect(url_for("post", post_id=post.post_id))
    elif request.method == "GET":
        form.post_title.data = post.post_title
        form.post_content.data = post.post_content
    return render_template("create_and_update_post.html", title="Update Post",
                           form=form, legend="게시글 업데이트")


# 게시글 삭제
@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user != current_user and current_user.user_type != "operator":
        abort(403)

    for post_comment in post.post_comments:
        db.session.delete(post_comment)
    db.session.commit()

    db.session.delete(post)
    db.session.commit()
    flash("게시글 삭제가 완료되었습니다!", "success")
    return redirect(url_for("home"))


# 작성자별 게시글 페이지
@app.route("/user/<string:user_id>")
def user_posts(user_id):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(id=user_id).first_or_404()
    posts = Post.query.filter_by(user=user)\
        .order_by(Post.post_datetime.desc())\
        .paginate(page=page, per_page=20)
    return render_template("user_posts.html", posts=posts, user=user)


# 게시글 댓글 업데이트
@app.route("/post/<int:post_id>/<int:post_comment_id>/update", methods=["GET", "POST"])
@login_required
def update_post_comment(post_id, post_comment_id):
    post = Post.query.get_or_404(post_id)
    page = request.args.get("page", 1, type=int)
    post_comments = PostComment.query.filter_by(post_comment_post_id=post_id) \
        .order_by(PostComment.post_comment_datetime.desc()).paginate(page=page, per_page=10)
    post_comment = PostComment.query.get_or_404(post_comment_id)
    if post_comment.user != current_user and current_user.user_type != "operator":
        abort(403)
    form = PostCommentForm()
    if form.validate_on_submit():
        post_comment.post_comment_content = form.post_comment_content.data
        db.session.commit()
        flash("댓글 수정이 완료되었습니다!", "success")
        return redirect(url_for("post", post_id=post_id))
    elif request.method == "GET":
        form.post_comment_content.data = post_comment.post_comment_content
    return render_template("post.html", title="Update Post Comment",
                           form=form, legend="댓글 업데이트", post=post, post_comments=post_comments,
                           post_id=post_id, post_comment_id=post_comment_id, action="update_comment")


# 게시글 댓글 삭제
@app.route("/post/<int:post_id>/<int:post_comment_id>delete", methods=["POST"])
@login_required
def delete_post_comment(post_id, post_comment_id):
    post_comment = PostComment.query.get_or_404(post_comment_id)
    if post_comment.user != current_user and current_user.user_type != "operator":
        abort(403)
    db.session.delete(post_comment)
    db.session.commit()
    flash("댓글이 성공적으로 삭제되었습니다!", "success")
    return redirect(url_for("post", post_id=post_id, action="delete_comment"))


# 공지 생성 페이지
@app.route("/notice/new", methods=["GET", "POST"])
@login_required
def new_notice():
    form = NoticeForm()
    if form.validate_on_submit():
        if form.notice_image.data:
            notice_image = save_and_return_image(form.notice_image.data, "notice_pics", (400, 400))
            notice_image = url_for("static", filename="notice_pics/" + notice_image)
        else:
            notice_image = "no_image"

        notice = Notice(notice_title=form.notice_title.data, notice_content=form.notice_content.data,
                        notice_writer_id=current_user.id, notice_image=notice_image)
        db.session.add(notice)
        db.session.commit()
        flash("공지글을 성공적으로 게시하였습니다!", "success")
        return redirect(url_for("home"))
    return render_template("create_and_update_notice.html", title="New Notice", form=form,
                           legend="공지글 게시")


# 공지사항
@app.route("/notice_board")
def notice_board():
    page = request.args.get("page", 1, type=int)
    notices = Notice.query.order_by(Notice.notice_datetime.desc()).paginate(page=page, per_page=20)
    return render_template("notice_board.html", title="Notice Board", notices=notices)


# 각각의 공지글
@app.route("/notice/<int:notice_id>")
def notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    notice.notice_page_view += 1
    db.session.commit()
    return render_template("notice.html", title=notice.notice_title, notice=notice)


# 공지글 업데이트 페이지
@app.route("/notice/<int:notice_id>/update", methods=["GET", "POST"])
@login_required
def update_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    if notice.user != current_user and current_user.user_type != "operator":
        abort(403)
    form = NoticeForm()
    if form.validate_on_submit():
        if form.notice_image.data:
            notice_image = save_and_return_image(form.notice_image.data, "notice_pics", (400, 400))
            notice_image = url_for("static", filename="notice_pics/" + notice_image)
            notice.notice_image = notice_image

        notice.notice_title = form.notice_title.data
        notice.notice_content = form.notice_content.data
        db.session.commit()
        flash("공지 업데이트가 완료되었습니다!", "success")
        return redirect(url_for("notice", notice_id=notice.notice_id))
    elif request.method == "GET":
        form.notice_title.data = notice.notice_title
        form.notice_content.data = notice.notice_content
    return render_template("create_and_update_notice.html", title="Update Notice",
                           form=form, legend="공지 업데이트")


# 공지글 삭제
@app.route("/notice/<int:notice_id>/delete", methods=["POST"])
@login_required
def delete_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    if notice.notice_writer_id != current_user.id and current_user.user_type != "operator":
        abort(403)
    db.session.delete(notice)
    db.session.commit()
    flash("공지글 삭제가 완료되었습니다!", "success")
    return redirect(url_for("home"))


# 오프라인 프로그램(친목도모회) 게시판
@app.route("/gathering_board", methods=["GET", "POST"])
def gathering_board():
    form = RegionSearchForm()
    page = request.args.get("page", 1, type=int)
    gatherings = Gathering.query.order_by(Gathering.gathering_uploaded_local_datetime.desc()).paginate(page=page, per_page=20)

    if form.validate_on_submit():
        region_search_term = form.region_search_term.data
        page = request.args.get("page", 1, type=int)
        gatherings = db.session.query(Gathering).filter(Gathering.gathering_address.contains(region_search_term)) \
                     .order_by(Gathering.gathering_uploaded_local_datetime.desc()).paginate(page=page, per_page=20)

        return render_template("gathering_board_on_region_search.html", title="Gathering Board",
                               gatherings=gatherings, region_search_term=region_search_term)

    return render_template("gathering_board.html", title="Gathering Board", form=form,
                           gatherings=gatherings)


# 지역 검색어를 입력한 결과의 오프라인 프로그램 게시판
@app.route("/gathering_board/<string:region_search_term>")
def gathering_board_on_region_search(region_search_term):
    page = request.args.get("page", 1, type=int)
    gatherings = db.session.query(Gathering).filter(Gathering.gathering_address.contains(region_search_term)) \
        .order_by(Gathering.gathering_uploaded_local_datetime.desc()).paginate(page=page, per_page=20)

    return render_template("gathering_board_on_region_search.html", title="Gathering Board",
                           gatherings=gatherings, region_search_term=region_search_term)


# 오프라인 프로그램(친목도모회) 생성 페이지
@app.route("/gathering/new", methods=["GET", "POST"])
@login_required
def new_gathering():
    form = GatheringForm()
    if form.validate_on_submit():
        if form.gathering_thumbnail.data:
            if form.gathering_thumbnail_form.data == "1":
                gathering_thumbnail = save_and_return_image(form.gathering_thumbnail.data, "gathering_pics", (200, 200))
            elif form.gathering_thumbnail_form.data == "2":
                gathering_thumbnail = save_and_return_image(form.gathering_thumbnail.data, "gathering_pics", None)
            gathering_thumbnail = url_for("static", filename="gathering_pics/" + gathering_thumbnail)
        else:
            gathering_thumbnail = url_for("static", filename="gathering_pics/default.jpg")

        gathering = Gathering(gathering_type=form.gathering_type.data, gathering_title=form.gathering_title.data,
                              gathering_content=form.gathering_content.data, gathering_address=form.gathering_address.data,
                              gathering_gym_manager_id=current_user.id,
                              gathering_start_local_datetime=form.gathering_start_local_datetime.data,
                              gathering_end_local_datetime=form.gathering_end_local_datetime.data,
                              gathering_max_participants_num=form.gathering_max_participants_num.data,
                              gathering_thumbnail=gathering_thumbnail)
        db.session.add(gathering)
        db.session.commit()
        flash("오프라인 프로그램을 성공적으로 게시하였습니다!", "success")
        return redirect(url_for("home"))
    return render_template("create_and_update_gathering.html", title="New Gathering", form=form,
                           legend="오프라인 프로그램 개최")


# 각각의 오프라인 프로그램(친목도모회)
# 신청, 신청 취소로 바꾸는 것도 가능 (나중에)
@app.route("/gathering/<int:gathering_id>", methods=["GET", "POST"])
def gathering(gathering_id):
    form = ApplyingGatheringForm()
    gathering = Gathering.query.get_or_404(gathering_id)
    if form.validate_on_submit():
        gathering.gathering_participants.append(current_user)
        gathering.gathering_current_participants_num += 1
        db.session.commit()
        flash("오프라인 프로그램 참가 신청을 하셨습니다!", "success")
        return redirect(url_for("home"))

    can_apply = True
    # 만약 이미 신청을 하였거나 주최자라면 신청이 불가능함
    if not current_user.is_authenticated:
        can_apply = False
    elif gathering in current_user.user_participating_gatherings or gathering.gathering_gym_manager_id == current_user.id:
        can_apply = False

    gathering_thumbnail = Image.open(app.root_path + "/" + gathering.gathering_thumbnail)
    thumbnail_width = np.array(gathering_thumbnail).shape[0]

    if thumbnail_width == 200:
        return render_template("gathering.html", title=gathering.gathering_title, form=form,
                               gathering=gathering, can_apply=can_apply)
    else:
        return render_template("gathering_poster.html", title=gathering.gathering_title, form=form,
                               gathering=gathering, can_apply=can_apply)


# 오프라인 프로그램 업데이트
@app.route("/gathering/<int:gathering_id>/update", methods=["GET", "POST"])
@login_required
def update_gathering(gathering_id):
    gathering = Gathering.query.get_or_404(gathering_id)
    if gathering.gathering_gym_manager_id != current_user.id and current_user.user_type != "operator":
        abort(403)
    form = GatheringForm()
    if form.validate_on_submit():
        if form.gathering_thumbnail.data:
            gathering_thumbnail = save_and_return_image(form.gathering_thumbnail.data, "gathering_pics", None)
            gathering_thumbnail = url_for("static", filename="gathering_pics/" + gathering_thumbnail)
            gathering.gathering_thumbnail = gathering_thumbnail
        gathering.gathering_title = form.gathering_title.data
        gathering.gathering_content = form.gathering_content.data
        gathering.gathering_type = form.gathering_type.data
        gathering.gathering_address = form.gathering_address.data
        gathering.gathering_start_local_datetime = form.gathering_start_local_datetime.data
        gathering.gathering_end_local_datetime = form.gathering_end_local_datetime.data
        gathering.gathering_max_participants_num = form.gathering_max_participants_num.data

        db.session.commit()
        flash("오프라인 프로그램 업데이트가 완료되었습니다!", "success")
        return redirect(url_for("gathering", gathering_id=gathering.gathering_id))
    elif request.method == "GET":
        form.gathering_title.data = gathering.gathering_title
        form.gathering_content.data = gathering.gathering_content
        form.gathering_type.data = gathering.gathering_type
        form.gathering_address.data = gathering.gathering_address
        form.gathering_start_local_datetime.data = gathering.gathering_start_local_datetime
        form.gathering_end_local_datetime.data = gathering.gathering_end_local_datetime
        form.gathering_max_participants_num.data = gathering.gathering_max_participants_num
        form.gathering_thumbnail.data = gathering.gathering_thumbnail

    return render_template("create_and_update_gathering.html", title="Update Gathering",
                           form=form, legend="오프라인 프로그램 업데이트")


# 오프라인 프로그램 삭제
@app.route("/gathering/<int:gathering_id>/delete", methods=["POST"])
@login_required
def delete_gathering(gathering_id):
    gathering = Gathering.query.get_or_404(gathering_id)
    if gathering.gathering_gym_manager_id != current_user.id and current_user.user_type != "operator":
        abort(403)
    db.session.delete(gathering)
    db.session.commit()
    flash("오프라인 프로그램 삭제가 완료되었습니다!", "success")
    return redirect(url_for("home"))


# 강의 생성 페이지
@app.route("/lecture/new", methods=["GET", "POST"])
@login_required
def new_lecture():
    form = LectureForm()
    if form.validate_on_submit():
        if form.lecture_open_local_date.data > form.lecture_close_local_date.data:
            flash("강의 종료 날짜가 강의 시작 날짜보다 앞섭니다!", "danger")
            return redirect(url_for('new_lecture'))

        if form.lecture_thumbnail.data:
            lecture_thumbnail = save_and_return_image(form.lecture_thumbnail.data, "lecture_pics", (200, 200))
            lecture_thumbnail = url_for("static", filename="lecture_pics/" + lecture_thumbnail)
        else:
            lecture_thumbnail = url_for("static", filename="lecture_pics/default.jpg")

        lecture = Lecture(lecture_type=form.lecture_type.data,
                          lecture_title=form.lecture_title.data,
                          lecture_content=form.lecture_content.data,
                          lecture_open_local_date=form.lecture_open_local_date.data,
                          lecture_close_local_date=form.lecture_close_local_date.data,
                          lecture_start_local_time=form.lecture_start_local_time.data,
                          lecture_end_local_time=form.lecture_end_local_time.data,
                          lecture_max_attendees_num=form.lecture_max_attendees_num.data,
                          lecture_thumbnail=lecture_thumbnail)
        db.session.add(lecture)
        db.session.commit()

        # 강의 요일들 또한 추가해줌
        recent_lecture = Lecture.query.order_by(Lecture.lecture_uploaded_datetime.desc()).first()
        lecture_days = form.lecture_days.data
        for lecture_day in lecture_days:
            lecture_day_instance = LectureDay(lecture_day_lecture_id=recent_lecture.lecture_id,
                                              lecture_day_lecture_day=lecture_day)
            db.session.add(lecture_day_instance)

        # 트레이너가 자신이 생성한 강의의 강의 트레이너로 등록됨
        teaching_contract = TeachingContract(trainer_id=current_user.id, lecture_id=recent_lecture.lecture_id,
                                             participation_type="teaching")
        db.session.add(teaching_contract)
        db.session.commit()

        flash("온라인 강의가 성공적으로 등록되었으며, 해당 강의의 강의 트레이너로 자동 등록되셨습니다.", "success")
        return redirect(url_for("home"))
    return render_template("create_and_update_lecture.html", title="New Lecture", form=form,
                           legend="강의 생성")


# 각각의 강의 페이지
@app.route("/lecture/<int:lecture_id>", methods=["GET", "POST"])
def lecture(lecture_id):
    form = ApplyingLectureForm()
    lecture = Lecture.query.get_or_404(lecture_id)
    if form.validate_on_submit():
        if form.submit1.data:
            teaching_contract = TeachingContract(trainer_id=current_user.id, lecture_id=lecture_id,
                                                 participation_type="feedback")
            db.session.add(teaching_contract)
            db.session.commit()
        elif form.submit2.data:
            # 각 요일의 출결 기록을 db에 저장함
            day_dict = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}

            lecture_days = []
            for lecture_day in lecture.lecture_days:
                lecture_days.append(lecture_day.lecture_day_lecture_day)

            date_and_days = []
            lecture_open_date = lecture.lecture_open_local_date
            lecture_close_date = lecture.lecture_close_local_date
            while True:
                if day_dict[lecture_open_date.weekday()] in lecture_days:
                    date_and_days.append((lecture_open_date, day_dict[lecture_open_date.weekday()]))
                lecture_open_date += timedelta(days=1)

                if lecture_open_date > lecture_close_date:
                    break

            for date, day in date_and_days:
                attendance = Attendance(attendance_trainee_id=current_user.id, attendance_lecture_id=lecture_id,
                                        attendance_lecture_local_date=date, attendance_lecture_local_day=day,
                                        attendance_has_attended=False)
                db.session.add(attendance)

            # 강의의 현재 수강 중인 인원 수를 1 늘려줌
            lecture.lecture_current_attendees_num += 1

            # 강의 수강 기록에 해당 회원을 올림
            lecture.lecture_attendees.append(current_user)
            db.session.commit()

    teaching_trainer_name = ""
    feedback_trainer_name = ""
    can_update_or_delete_lecture = False
    can_register_as_feedback_trainer = False
    can_register_as_attendee = False

    if len(lecture.trainers) < 2:
        teaching_trainer_name = lecture.trainers[0].trainer.user_name
        if lecture.trainers[0].trainer_id != current_user.id:
            can_register_as_feedback_trainer = True
        elif lecture.trainers[0].trainer_id == current_user.id or current_user.user_type == "operator":
            can_update_or_delete_lecture = True
    # 강의 트레이너와 피드백 트레이너가 모두 있는 경우
    else:
        for teaching_contract in lecture.trainers:
            if teaching_contract.participation_type == "teaching":
                teaching_trainer_name = teaching_contract.trainer.user_name
            elif teaching_contract.participation_type == "feedback":
                feedback_trainer_name = teaching_contract.trainer.user_name
        # 일반회원이 아직 강의를 등록 안했으며 현재 강의 참여 인원수가 최대 인원수보다 낮으며, 해당 일반회원이 이미 참여하지 않은 경우
        if current_user.user_type == "trainee":
            if lecture not in current_user.user_attending_lectures:
                if (lecture.lecture_max_attendees_num == 0 or
                        (lecture.lecture_current_attendees_num < lecture.lecture_max_attendees_num)):
                    can_register_as_attendee = True

    return render_template("lecture.html", title=lecture.lecture_id, lecture=lecture,
                           form=form,
                           teaching_trainer_name=teaching_trainer_name,
                           feedback_trainer_name=feedback_trainer_name,
                           can_update_or_delete_lecture=can_update_or_delete_lecture,
                           can_register_as_feedback_trainer=can_register_as_feedback_trainer,
                           can_register_as_attendee=can_register_as_attendee
                           )


# 강의 업데이트 페이지
@app.route("/lecture/<int:lecture_id>/update", methods=["GET", "POST"])
@login_required
def update_lecture(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    if current_user.id != lecture.trainers[0].trainer_id:
        abort(403)
    form = LectureForm()
    if form.validate_on_submit():
        if form.lecture_thumbnail.data:
            lecture_thumbnail = save_and_return_image(form.lecture_thumbnail.data, "lecture_pics", (200, 200))
            lecture_thumbnail = url_for("static", filename="lecture_pics/" + lecture_thumbnail)
            lecture.lecture_thumbnail = lecture_thumbnail
        lecture.lecture_title = form.lecture_title.data
        lecture.lecture_content = form.lecture_content.data
        lecture.lecture_open_local_date = form.lecture_open_local_date.data
        lecture.lecture_close_local_date = form.lecture_close_local_date.data
        lecture.lecture_start_local_time = form.lecture_start_local_time.data
        lecture.lecture_end_local_time = form.lecture_end_local_time.data
        lecture.lecture_max_attendees_num = form.lecture_max_attendees_num.data

        db.session.commit()
        flash("강의 업데이트가 완료되었습니다!", "success")
        return redirect(url_for("lecture", lecture_id=lecture.lecture_id))
    elif request.method == "GET":
        form.lecture_title.data = lecture.lecture_title
        form.lecture_content.data = lecture.lecture_content
        form.lecture_open_local_date.data = lecture.lecture_open_local_date
        form.lecture_close_local_date.data = lecture.lecture_close_local_date
        form.lecture_start_local_time.data = lecture.lecture_start_local_time
        form.lecture_end_local_time.data = lecture.lecture_end_local_time
        form.lecture_max_attendees_num.data = lecture.lecture_max_attendees_num
        form.lecture_thumbnail.data = lecture.lecture_thumbnail

    return render_template("create_and_update_lecture.html", title="Update Lecture",
                           form=form, legend="강의 업데이트")


# 강의 등록 취소 페이지
@app.route("/lecture/<int:lecture_id>/delete", methods=["POST"])
@login_required
def delete_lecture(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)

    if current_user.id != lecture.trainers[0].trainer_id and current_user.user_type != "operator":
        abort(403)

    # 트레이너가 강의 트레이너로 등록한 기록 제거
    db.session.delete(lecture.trainers[0])
    db.session.commit()

    # 해당 강의의 요일들 제거
    for lecture_day in lecture.lecture_days:
        db.session.delete(lecture_day)
        db.session.commit()

    # 해당 강의 제거
    db.session.delete(lecture)
    db.session.commit()
    flash("강의 등록 취소가 완료되었습니다!", "success")
    return redirect(url_for("home"))


# 일반회원의 일정관리 페이지
@app.route("/trainee_schedule")
@login_required
def trainee_schedule():
    if current_user.user_type != "trainee":
        abort(403)

    lectures = Lecture.query.all()

    # 본인이 참여하고 있는 강의들
    attending_lectures = []
    for user_attending_lecture in current_user.user_attending_lectures:
        lecture_days = []
        for lecture_day in user_attending_lecture.lecture_days:
            lecture_days.append(lecture_day.lecture_day_lecture_day)
        lecture_days = ", ".join(lecture_days)
        attending_lectures.append((user_attending_lecture, lecture_days))

    odd_index_lectures = []
    even_index_lectures = []
    if len(attending_lectures) >= 1:
        for index, lecture in enumerate(attending_lectures):
            if index % 2 != 1:
                odd_index_lectures.append(lecture)
            else:
                even_index_lectures.append(lecture)

        if len(attending_lectures) % 2 == 1:
            even_index_lectures.append(("", ""))
    lectures = list(zip(odd_index_lectures, even_index_lectures))
    gatherings = current_user.user_participating_gatherings

    return render_template("trainee_schedule.html", title="Trainee Schedule", lectures=lectures, gatherings=gatherings)


# 트레이너의 일정관리 페이지
@app.route("/trainer_schedule")
@login_required
def trainer_schedule():
    if current_user.user_type != "trainer":
        abort(403)
    lectures = Lecture.query.all()

    # 본인이 강의 트레이너로 있는 피드백 트레이너의 등록을 대기하는 강의들
    waiting_lectures = []
    activated_lectures = []
    for lecture in lectures:
        is_included = False
        for teaching_contract in lecture.trainers:
            if current_user.id == teaching_contract.trainer_id:
                lecture_days = []
                for lecture_day in lecture.lecture_days:
                    lecture_days.append(lecture_day.lecture_day_lecture_day)

                lecture_days = ", ".join(lecture_days)
                participation_type = teaching_contract.participation_type
                is_included = True

        if is_included:
            if len(lecture.trainers) == 1:
                waiting_lectures.append((lecture, lecture_days, participation_type))
            else:
                activated_lectures.append((lecture, lecture_days, participation_type))

    # 피드백 트레이너를 대기하는 강의들
    odd_index_waiting_lectures = []
    even_index_waiting_lectures = []
    if len(waiting_lectures) >= 1:
        for index, lecture in enumerate(waiting_lectures):
            if index % 2 != 1:
                odd_index_waiting_lectures.append(lecture)
            else:
                even_index_waiting_lectures.append(lecture)

        if len(waiting_lectures) % 2 == 1:
            even_index_waiting_lectures.append(("", ""))
    waiting_lectures = list(zip(odd_index_waiting_lectures, even_index_waiting_lectures))

    # activate된 강의들 (일반회원이 신청 가능해지며, 강의내용 수정 및 삭제가 불가능해짐)
    odd_index_activated_lectures = []
    even_index_activated_lectures = []
    if len(activated_lectures) >= 1:
        for index, lecture in enumerate(activated_lectures):
            if index % 2 != 1:
                odd_index_activated_lectures.append(lecture)
            else:
                even_index_activated_lectures.append(lecture)

        if len(lectures) % 2 == 1:
            even_index_activated_lectures.append(("", ""))
    activated_lectures = list(zip(odd_index_activated_lectures, even_index_activated_lectures))

    gatherings = current_user.user_participating_gatherings

    return render_template("trainer_schedule.html", title="Trainer Schedule", waiting_lectures=waiting_lectures,
                           activated_lectures=activated_lectures, gatherings=gatherings)


# 트레이너가 피드백 트레이너로 등록할 수 있는 강의들을 보여주는 페이지
@app.route("/trainer_registering_lecture")
@login_required
def trainer_registering_lecture():
    if current_user.user_type != "trainer":
        abort(403)

    lectures = Lecture.query.all()

    # 트레이너의 경우 아직 피드백 트레이너가 없으며, 본인이 강의 트레이너로 참여하지 않고 있는 강의에 피드백 트레이너로 참여 가능함
    no_feedback_trainer_lectures = []
    for lecture in lectures:
        if len(lecture.trainers) == 1:
            if lecture.trainers[0].trainer_id != current_user.id:
                lecture_days = []
                for lecture_day in lecture.lecture_days:
                    lecture_days.append(lecture_day.lecture_day_lecture_day)

                lecture_days = ", ".join(lecture_days)
                no_feedback_trainer_lectures.append((lecture, lecture_days))

    odd_index_lectures = []
    even_index_lectures = []
    if len(no_feedback_trainer_lectures) >= 1:
        for index, lecture in enumerate(no_feedback_trainer_lectures):
            if index % 2 != 1:
                odd_index_lectures.append(lecture)
            else:
                even_index_lectures.append(lecture)

        if len(no_feedback_trainer_lectures) % 2 == 1:
            even_index_lectures.append(("", ""))
    lectures = list(zip(odd_index_lectures, even_index_lectures))

    return render_template("registering_lecture.html", title="Trainer Registering Lecture",
                           legend="피드백 트레이너로 참여 가능 강의 목록", lectures=lectures)


# 일반회원이 수강생으로 등록할 수 있는 강의들을 보여주는 페이지
@app.route("/trainee_registering_lecture/<string:lecture_type>")
def trainee_registering_lecture(lecture_type="전체"):
    if lecture_type == "전체":
        lectures = Lecture.query.all()
    else:
        lectures = Lecture.query.filter_by(lecture_type=lecture_type)

    # 일반회원의 경우 강의 트레이너와 피드백 트레이너가 모두 있으며, 이미 수강한 강의가 아니며 최대 인원이 다 차지 않은 경우 수강생으로 등록 가능함
    available_to_be_enrolled_lectures = []
    for lecture in lectures:
        if len(lecture.trainers) == 2:
            is_already_enrolled = False
            if current_user.user_type == "trainee":
                for attending_lecture in current_user.user_attending_lectures:
                    if attending_lecture.lecture_id == lecture.lecture_id:
                        is_already_enrolled = True
                        break
            if not is_already_enrolled:
                if (lecture.lecture_max_attendees_num == 0 or
                        lecture.lecture_current_attendees_num < lecture.lecture_max_attendees_num):
                    lecture_days = []
                    for lecture_day in lecture.lecture_days:
                        lecture_days.append(lecture_day.lecture_day_lecture_day)
                    lecture_days = ", ".join(lecture_days)
                    available_to_be_enrolled_lectures.append((lecture, lecture_days))

    odd_index_lectures = []
    even_index_lectures = []
    if len(available_to_be_enrolled_lectures) >= 1:
        for index, lecture in enumerate(available_to_be_enrolled_lectures):
            if index % 2 != 1:
                odd_index_lectures.append(lecture)
            else:
                even_index_lectures.append(lecture)

        if len(available_to_be_enrolled_lectures) % 2 == 1:
            even_index_lectures.append(("", ""))
    lectures = list(zip(odd_index_lectures, even_index_lectures))

    return render_template("registering_lecture.html", title="Trainee Registering Lecture",
                           legend="수강 가능한 강의 목록", lectures=lectures, lecture_type=lecture_type)


# 일반회원의 각 강의별 출결 현황을 보여주는 페이지
@app.route("/attendance_list/<string:trainee_id>/<int:lecture_id>")
@login_required
def attendance_list(trainee_id, lecture_id):
    if current_user.user_type != "trainee":
        abort(403)
    page = request.args.get("page", 1, type=int)
    attendances = Attendance.query.filter_by(attendance_trainee_id=trainee_id, attendance_lecture_id=lecture_id).\
        order_by(Attendance.attendance_lecture_local_date).paginate(page=page, per_page=20)
    lecture_title = Lecture.query.get_or_404(lecture_id).lecture_title

    return render_template("attendance_list.html", title="Attendance List", lecture_title=lecture_title,
                           attendances=attendances, trainee_id=trainee_id, lecture_id=lecture_id)