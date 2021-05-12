from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField,BooleanField, RadioField, SelectMultipleField, TextAreaField,\
    IntegerField, DateField, DateTimeField
from wtforms.validators import DataRequired, Required, Length, Email, EqualTo, ValidationError
from healthton.models import User


class RegistrationForm(FlaskForm):
    user_id = StringField("아이디",
                          validators=[DataRequired(), Length(min=2, max=20)])
    user_name = StringField("닉네임(이름)",
                            validators=[DataRequired(), Length(min=2, max=20)])
    user_email = StringField("이메일 주소",
                             validators=[DataRequired(), Email()])
    user_password = PasswordField("비밀번호", validators=[DataRequired()])
    user_confirm_password = PasswordField("비밀번호 확인",
                                          validators=[DataRequired(), EqualTo("user_password")])  # 확인 용도로만 사용함
    user_gender = RadioField("성별", coerce=str, choices=[("1", "남성"), ("2", "여성")])
    user_address = StringField("주소")
    user_type = RadioField("분류", coerce=str, choices=[("trainee", "일반회원"), ("trainer", "트레이너"),
                                                      ("gym_manager", "헬스장 관리자")])
    trainer_major = StringField("분야")  # 트레이너의 경우 한정
    business_license_number = StringField("사업자등록번호(###-##-#####)")  # 헬스장 메니저의 경우 한정
    submit = SubmitField('Sign Up')

    def validate_user_id(self, user_id):
        user = User.query.filter_by(id=user_id.data).first()
        if user:
            raise ValidationError("That ID is taken. Please choose a different one.")

    def validate_user_name(self, user_name):
        user = User.query.filter_by(user_name=user_name.data).first()
        if user:
            raise ValidationError("That user name is taken. Please choose a different one.")

    def validate_user_email(self, user_email):
        user = User.query.filter_by(user_email=user_email.data).first()
        if user:
            raise ValidationError("That email is taken. Please choose a different one.")


class LoginForm(FlaskForm):
    user_id = StringField("아이디", validators=[DataRequired()])
    user_password = PasswordField("비밀번호", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("로그인")


class UpdateAccountForm(FlaskForm):
    user_profile_content = TextAreaField("프로필 글 수정", validators=[Length(max=1000)], render_kw={'class': 'form-control', 'rows': 5})
    user_profile_image = FileField("프로필 사진 수정", validators=[FileAllowed(["jpg", "png"])])
    user_name = StringField("닉네임(이름)", validators=[DataRequired(), Length(min=2, max=20)])
    user_email = StringField("이메일 주소", validators=[DataRequired(), Email()])

    submit = SubmitField("업데이트")

    def validate_user_name(self, user_name):
        if user_name.data != current_user.user_name:
            user = User.query.filter_by(user_name=user_name.data).first()
            if user:
                raise ValidationError("That user name is taken. Please choose a different one.")

    def validate_user_email(self, user_email):
        if user_email.data != current_user.user_email:
            user = User.query.filter_by(user_email=user_email.data).first()
            if user:
                raise ValidationError("That email is taken. Please choose a different one.")


class PostForm(FlaskForm):
    post_title = StringField("Title", validators=[DataRequired()])
    post_content = TextAreaField("Content", validators=[DataRequired()], render_kw={'class': 'form-control', 'rows': 5})
    post_image = FileField("이미지 첨부", validators=[FileAllowed(["jpg", "png"])])
    submit = SubmitField("게시")


class PostCommentForm(FlaskForm):
    post_comment_content = TextAreaField("", validators=[DataRequired()])
    submit1 = SubmitField("댓글 등록")
    submit2 = SubmitField("댓글 수정")


class NoticeForm(FlaskForm):
    notice_title = StringField("Title", validators=[DataRequired()])
    notice_content = TextAreaField("Content", validators=[DataRequired()], render_kw={'class': 'form-control', 'rows': 5})
    notice_image = FileField("이미지 첨부", validators=[FileAllowed(["jpg", "png"])])
    submit = SubmitField("게시")


class GatheringForm(FlaskForm):
    gathering_type = StringField("종류", validators=[DataRequired()])
    gathering_title = StringField("제목", validators=[DataRequired()])
    gathering_content = TextAreaField("내용", validators=[DataRequired()], render_kw={'class': 'form-control', 'rows': 5})
    gathering_thumbnail = FileField("썸네일 업로드", validators=[FileAllowed(["jpg", "png"])])
    gathering_address = StringField("개최지 주소", validators=[DataRequired()])
    gathering_start_local_datetime = DateField("시작일 (예시: 2020-5-30)", format="%Y-%m-%d", validators=[DataRequired()])
    gathering_end_local_datetime = DateField("종료일 (예시: 2020-6-01)", format="%Y-%m-%d")
    gathering_max_participants_num = IntegerField("최대 인원수")
    gathering_thumbnail_form = RadioField("이미지 양식 종류", coerce=str, choices=[("1", "썸네일"), ("2", "포스터")])
    submit = SubmitField("게시")


class ApplyingGatheringForm(FlaskForm):
    submit = SubmitField("신청")


class RegionSearchForm(FlaskForm):
    region_search_term = StringField("지역 검색어 입력", validators=[DataRequired()])
    submit = SubmitField("Search")


class LectureForm(FlaskForm):
    lecture_type = RadioField("강의 종류", coerce=str, choices=[("고체중 다이어트", "고체중 다이어트"), ("남자 요가", "남자 요가"),
                                                            ("다이어트", "다이어트"), ("근력 운동", "근력 운동")])
    lecture_title = StringField("강의 제목", validators=[DataRequired()])
    lecture_content = TextAreaField("강의 내용", validators=[DataRequired()], render_kw={'class': 'form-control', 'rows': 5})
    lecture_thumbnail = FileField("썸네일 업로드", validators=[FileAllowed(["jpg", "png"])])
    lecture_open_local_date = DateField("시작일 (예시: 2020-5-30)", format="%Y-%m-%d", validators=[DataRequired()])
    lecture_close_local_date = DateField("종료일 (예시: 2020-6-20)", format="%Y-%m-%d", validators=[DataRequired()])
    lecture_start_local_time = DateTimeField("시작 시간 (예시: 12:00)", format="%H:%M", validators=[DataRequired()])
    lecture_end_local_time = DateTimeField("종료 시간 (예시: 13:00)", format="%H:%M", validators=[DataRequired()])
    lecture_days = SelectMultipleField("강의 요일 (Ctrl 키로 여러 요일 선택 가능)", choices=[("월", "월"), ("화", "화"), ("수", "수"), ("목", "목"),
                                                 ("금", "금"), ("토", "토"), ("일", "일")])
    lecture_max_attendees_num = IntegerField("최대 인원수 (제한 없을시 0 입력)", default=0)
    submit = SubmitField("강의 등록")


class ApplyingLectureForm(FlaskForm):
    submit1 = SubmitField("피드백 트레이너로 등록")
    submit2 = SubmitField("강의 수강 신청")