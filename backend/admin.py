from sqladmin import Admin, ModelView
from backend.models import User, Team, Task, Meeting, Evaluation, Comment
from backend.models.base import engine
from backend.main import app


class UserAdmin(ModelView, model=User):
    """
        Админ‑панель для управления пользователями.

        Настройки:
            - column_list: отображаемые поля (id, email, full_name, role, team_id).
            - form_excluded_columns: исключает поле hashed_password из формы.
            - column_details_exclude_list: исключает hashed_password из деталей.
            - can_delete: разрешено удаление пользователей.
        """

    column_list = [User.id, User.email, User.full_name, User.role, User.team_id]
    form_excluded_columns = [User.hashed_password]
    column_details_exclude_list = [User.hashed_password]
    can_delete = True


class TeamAdmin(ModelView, model=Team):
    """
        Админ‑панель для управления командами.

        Настройки:
            - column_list: отображаемые поля (id, name, admin_id).
            - form_ajax_refs: позволяет искать админа по email и full_name.
        """

    column_list = [Team.id, Team.name, Team.admin_id]
    form_ajax_refs = {
        "admin": {
            "fields": ("email", "full_name"),
        }
    }


class TaskAdmin(ModelView, model=Task):
    """
        Админ‑панель для управления задачами.

        Настройки:
            - column_list: отображаемые поля (id, title, status, deadline, creator_id, assignee_id).
            - form_ajax_refs: позволяет искать создателя, исполнителя и команду по email/name.
        """

    column_list = [Task.id, Task.title, Task.status, Task.deadline, Task.creator_id, Task.assignee_id]
    form_ajax_refs = {
        "creator": {"fields": ("email",)},
        "assignee": {"fields": ("email",)},
        "team": {"fields": ("name",)},
    }


class MeetingAdmin(ModelView, model=Meeting):
    """
        Админ‑панель для управления встречами.

        Настройки:
            - column_list: отображаемые поля (id, title, start_time, end_time, creator_id).
        """

    column_list = [Meeting.id, Meeting.title, Meeting.start_time, Meeting.end_time, Meeting.creator_id]


class EvaluationAdmin(ModelView, model=Evaluation):
    """
        Админ‑панель для управления оценками.

        Настройки:
            - column_list: отображаемые поля (id, score, task_id, evaluator_id, evaluated_user_id, created_at).
        """

    column_list = [Evaluation.id, Evaluation.score, Evaluation.task_id, Evaluation.evaluator_id, Evaluation.evaluated_user_id, Evaluation.created_at]


class CommentAdmin(ModelView, model=Comment):
    """
        Админ‑панель для управления комментариями.

        Настройки:
            - column_list: отображаемые поля (id, content, task_id, author_id).
        """

    column_list = [Comment.id, Comment.content, Comment.task_id, Comment.author_id]


admin = Admin(app, engine)


admin.add_view(UserAdmin)
admin.add_view(TeamAdmin)
admin.add_view(TaskAdmin)
admin.add_view(MeetingAdmin)
admin.add_view(EvaluationAdmin)
admin.add_view(CommentAdmin)