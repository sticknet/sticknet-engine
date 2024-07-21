from .models import Report, Feedback, Question, Error, UserReport, PostReport, PublicFile
from sticknet.admin_site import admin_site

admin_site.register(Report)
admin_site.register(Feedback)
admin_site.register(Question)
admin_site.register(Error)
admin_site.register(UserReport)
admin_site.register(PostReport)
admin_site.register(PublicFile)
