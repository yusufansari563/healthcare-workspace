from sqladmin import Admin, ModelView
from src.models.models import Appointment, AppointmentType, User

# Define your ModelViews
class AppointmentTypeAdmin(ModelView, model=AppointmentType):
    column_list = [AppointmentType.id, AppointmentType.name, AppointmentType.type, AppointmentType.price]
    icon = "fa-solid fa-stethoscope"

class AppointmentAdmin(ModelView, model=Appointment):
    column_list = [Appointment.id, Appointment.appointment_type_id, Appointment.begins_at, Appointment.ends_at, Appointment.price]
    icon = "fa-solid fa-calendar-check"

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.full_name]
    icon = "fa-solid fa-user"
    column_searchable_list = [User.email, User.full_name]

# Create a setup function to initialize and attach the admin panel
def setup_admin(app, engine):
    admin = Admin(app, engine)
    
    # Register the views
    admin.add_view(AppointmentTypeAdmin)
    admin.add_view(AppointmentAdmin)
    admin.add_view(UserAdmin)
    
    return admin