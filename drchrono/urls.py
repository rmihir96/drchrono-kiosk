from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib import admin
admin.autodiscover()

import views


urlpatterns = [
    url(r'^setup/$', views.SetupView.as_view(), name='setup'),
    url(r'^welcome/$', views.DoctorWelcome.as_view(), name='welcome'),
    url(r'^appointment/$', views.CheckAppointments.as_view(), name='appointment'),
    url(r'^appointment/(?P<appid>\d+)/$', views.arrived, name='arrived'),
    url(r'^schedule/$', views.ScheduledAppointments.as_view(), name='schedule'),
    url(r'^schedule/(?P<appid>\d+)/$', views.see_patient, name='see_patient'),
    url(r'^complete/(?P<app_id>\d+)/$', views.appointment_complete, name='complete'),
    url(r'^patient_checkin/$', views.patient_checkin, name='checkin'),
    # url(r'^create_appointment/$', views.create_appointment, name='create_appointment'),
    url(r'^update_info/$', views.update_patient, name='update'),
    # url(r'^arrived/$', views.update_patient, name='arrived'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
]