from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from social_django.models import UserSocialAuth
from .forms import CheckinForm, UpdatePatientInfo
from drchrono.endpoints import DoctorEndpoint, AppointmentEndpoint, PatientEndpoint, AppointmentProfileEndpoint
from .models import Appointments

from dateutil import parser as date_parser

import datetime
import pytz

class SetupView(TemplateView):
    """
    The beginning of the OAuth sign-in flow. Logs a user into the kiosk, and saves the token.
    """
    template_name = 'kiosk_setup.html'


class DoctorWelcome(TemplateView):
    """
    The doctor can see what appointments they have today.
    """
    template_name = 'doctor_welcome.html'

    def get_token(self):
        """
        Social Auth module is configured to store our access tokens. This dark magic will fetch it for us if we've
        already signed in.
        """
        oauth_provider = UserSocialAuth.objects.get(provider='drchrono')
        access_token = oauth_provider.extra_data['access_token']
        return access_token

    def make_api_request(self):
        """
        Use the token we have stored in the DB to make an API request and get doctor details. If this succeeds, we've
        proved that the OAuth setup is working
        """
        # We can create an instance of an endpoint resource class, and use it to fetch details
        access_token = self.get_token()
        api = DoctorEndpoint(access_token)
        # Grab the first doctor from the list; normally this would be the whole practice group, but your hackathon
        # account probably only has one doctor in it.
        return next(api.list())

    def get_context_data(self, **kwargs):
        kwargs = super(DoctorWelcome, self).get_context_data(**kwargs)
        # Hit the API using one of the endpoints just to prove that we can
        # If this works, then your oAuth setup is working correctly.
        doctor_details = self.make_api_request()
        kwargs['doctor'] = doctor_details
        return kwargs


class CheckAppointments(TemplateView):
    """docstring for ClassName"""
    
    template_name = 'appointments.html'

    def get_token(self):
        """
        Social Auth module is configured to store our access tokens. This dark magic will fetch it for us if we've
        already signed in.
        """
        oauth_provider = UserSocialAuth.objects.get(provider='drchrono')
        access_token = oauth_provider.extra_data['access_token']
        return access_token

    def make_api_request(self):
        """
        Use the token we have stored in the DB to make an API request and get doctor details. If this succeeds, we've
        proved that the OAuth setup is working
        """
        # We can create an instance of an endpoint resource class, and use it to fetch details
        access_token = self.get_token()
        api = AppointmentEndpoint(access_token)
        # Grab the first doctor from the list; normally this would be the whole practice group, but your hackathon
        # account probably only has one doctor in it.
        return (api.list(date = "2019-10-22"))

    def get_context_data(self, **kwargs):
        # print(kwargs, kwargs['flag'])
        # print(self.request.session['user_id'])
        kwargs = super(CheckAppointments, self).get_context_data(**kwargs)
        
        # Hit the API using one of the endpoints just to prove that we can
        # If this works, then your oAuth setup is working correctly.
        appnt = self.make_api_request()
        # print(appnt.next())

        for app in appnt:
            appointment_obj, created_now = Appointments.objects.get_or_create(
                appointment_id = app['id'],
                patient_id = app['patient']
            )

            if created_now:
                appointment_obj.time_waited = None
                
            appointment_obj.status = app['status']
            appointment_obj.scheduled_time = app['scheduled_time']
            appointment_obj.save()
            appointment_obj.scheduled_time = date_parser.parse(app['scheduled_time'])
        
        if 'flag' in kwargs:
            return appnt

        kwargs['appointment'] = self.filter(appnt, self.request.session['user_id'])
        # kwargs['appointment'] = Appointments.objects.get(patient_id = self.request.session['user_id'])

        return kwargs

    def update_appointment_status(self, id, data):
        access_token = self.get_token()
        api = AppointmentEndpoint(access_token)
        api.update(id, data)
    
    def filter(self, appointments, patient_id):
        print("Patient id", patient_id)
        print(appointments)
        data = []
        for appointment in appointments:
            print(appointment)
            if appointment['patient'] == patient_id:
                data.append(appointment)
        # print(data)
        return data

    

    



class PatientDetails(TemplateView):
    """docstring for ClassName"""
    
    template_name = 'appointments.html'

    def get_token(self):
        """
        Social Auth module is configured to store our access tokens. This dark magic will fetch it for us if we've
        already signed in.
        """
        oauth_provider = UserSocialAuth.objects.get(provider='drchrono')
        access_token = oauth_provider.extra_data['access_token']
        return access_token

    def make_api_request(self):
        """
        Use the token we have stored in the DB to make an API request and get doctor details. If this succeeds, we've
        proved that the OAuth setup is working
        """
        # We can create an instance of an endpoint resource class, and use it to fetch details
        access_token = self.get_token()
        api = PatientEndpoint(access_token)
        # Grab the first doctor from the list; normally this would be the whole practice group, but your hackathon
        # account probably only has one doctor in it.
        return (api.list())

    def get_context_data(self, **kwargs):
        kwargs = super(PatientDetails, self).get_context_data(**kwargs)
        # Hit the API using one of the endpoints just to prove that we can
        # If this works, then your oAuth setup is working correctly.
        patients = self.make_api_request()

        kwargs['appointment'] = patients
        return patients

    def update_request(self, id ,data):
        access_token = self.get_token()
        api = PatientEndpoint(access_token)
        api.update(id, data)

    def get_patient(self, id):
        access_token = self.get_token()
        api = PatientEndpoint(access_token)
        return api.fetch(id)
       

    
class ScheduledAppointments(TemplateView):
    template_name = 'schedule.html'

    # def get_patients(self):
    #     appointments = CheckAppointments().get_context_data(flag = True)
    #     patients = PatientDetails()
    #     patient_data = []
    #     arrived_patient_data = []
    #     for appointment in appointments:
    #         # print(appointment)
    #         patient = patients.get_patient(appointment['patient'])
           
    #         patient_data.append({'name' : patient['first_name'], 'surname' : patient['last_name'], 'appointment_time': appointment['scheduled_time'], 'status' : appointment['status'] })
        
    #     return patient_data, arrived_patient_data

    def get_context_data(self, **kwargs):
        kwargs = super(ScheduledAppointments, self).get_context_data(**kwargs)
        # Hit the API using one of the endpoints just to prove that we can
        # If this works, then your oAuth setup is working correctly.
        # patients, checkedin = self.get_patients()

        kwargs['schedule'] = Appointments.objects.all()
        # kwargs['checkedin'] = checkedin
        return kwargs









def patient_checkin(request):
    # if this is a POST request we need to process the form data
    
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = CheckinForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            fname = form.cleaned_data['first_name']
            lname = form.cleaned_data['last_name']
            dob = form.cleaned_data['dob']
            # print(dob)
            
            p = PatientDetails()
            plist = p.get_context_data()
            
            status, data = check_patient_details(request, plist, fname, lname, dob)
            if status == '0': #Never set earlier (First Time user!)
                return redirect('/update_info/')
            
            elif status == '1':
                return render(request, 'update_decision.html', {'data' : data})  
            else:
                print('user not found!')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = CheckinForm()

    return render(request, 'checkin.html', {'form': form})

# Function to check if Patient is valid:

def check_patient_details(request, patient_list, fname, lname, dob):
    print(str(fname), lname, str(dob))
    for idx, patient in enumerate(patient_list):
        if patient['first_name'] == fname and patient['last_name'] == lname and patient['date_of_birth'] == str(dob):
            request.session['user_id'] = patient['id']
            if patient['address'] and patient['cell_phone'] and patient['email']:
                return ('1', {'address' : patient['address'], 'email' : patient['email'], 'phone' : patient['cell_phone']})
            else:
                return ('0', {})
            
    return False



def update_patient(request):
# if this is a POST request we need to process the form data

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = UpdatePatientInfo(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:

            address = form.cleaned_data['address']
            pno = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            data = {'address' : address,
                    'email' : email,
                    'cell_phone' : pno
                    }
            print(request.session['user_id'] )
            
            p =  PatientDetails()
            p.update_request(request.session['user_id'] , data)
            return redirect('/appointment/')
            

            # return redirect('/welcome/')
            

    # if a GET (or any other method) we'll create a blank form
    else:
        form = UpdatePatientInfo()

    return render(request, 'updateinfo.html', {'form': form})



def arrived(request, appid):
        if request.method == 'POST':
            # appointment_id =  request.POST.get("appid", "")
            print("appointment id:", appid)
            app = CheckAppointments()
            app.update_appointment_status(appid, {'status' : 'Arrived'})
            appointment_obj = Appointments.get(appointment_id = appid)
            appointment_obj.status = "Arrived"
            appointment_obj.arrival_time = get_local_datetime(request)
            appointment_obj.reference_time = get_local_datetime(request)
            return redirect('/appointment/')





def get_local_datetime(request):
    user_timezone = request.COOKIES.get('tzname_from_user', 'UTC')
    return datetime.datetime.now(pytz.timezone(user_timezone))
