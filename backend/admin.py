from sqladmin import Admin, ModelView
from backend.models import User, Team, Task, Meeting, Evaluation, Comment
from backend.models.base import engine
from backend.main import app


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.full_name, User.role, User.team_id]
    form_excluded_columns = [User.hashed_password]
    column_details_exclude_list = [User.hashed_password]
    can_delete = True


class TeamAdmin(ModelView, model=Team):
    column_list = [Team.id, Team.name, Team.admin_id]
    form_ajax_refs = {
        "admin": {
            "fields": ("email", "full_name"),
        }
    }


class TaskAdmin(ModelView, model=Task):
    column_list = [Task.id, Task.title, Task.status, Task.deadline, Task.creator_id, Task.assignee_id]
    form_ajax_refs = {
        "creator": {"fields": ("email",)},
        "assignee": {"fields": ("email",)},
        "team": {"fields": ("name",)},
    }


class MeetingAdmin(ModelView, model=Meeting):
    column_list = [Meeting.id, Meeting.title, Meeting.start_time, Meeting.end_time, Meeting.creator_id]


class EvaluationAdmin(ModelView, model=Evaluation):
    column_list = [Evaluation.id, Evaluation.score, Evaluation.task_id, Evaluation.evaluator_id, Evaluation.evaluated_user_id]


class CommentAdmin(ModelView, model=Comment):
    column_list = [Comment.id, Comment.content, Comment.task_id, Comment.author_id]


admin = Admin(app, engine)


admin.add_view(UserAdmin)
admin.add_view(TeamAdmin)
admin.add_view(TaskAdmin)
admin.add_view(MeetingAdmin)
admin.add_view(EvaluationAdmin)
admin.add_view(CommentAdmin)