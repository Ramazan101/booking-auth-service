from sqladmin import Admin
from booking.database.db import engine
from booking.admin.views import UserAdmin

def setup_admin(app):
    admin = Admin(app, engine)

    admin.add_view(UserAdmin)