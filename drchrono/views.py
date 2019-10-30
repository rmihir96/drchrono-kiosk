from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from social_django.models import UserSocialAuth
from .forms import CheckinForm, UpdatePatientInfo
from drchrono.endpoints import DoctorEndpoint, AppointmentEndpoint, PatientEndpoint, AppointmentProfileEndpoint
from .models import Appointments
from django.db.models import Q
from dateutil import parser as date_parser

from datetime import datetime, timedelta

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


class CheckAppointments(DoctorWelcome, TemplateView):
    """docstring for ClassName"""
    
    template_name = 'appointments.html'



    def appointment_api_request(self):
        """
        Use the token we have stored in the DB to make an API request and get doctor details. If this succeeds, we've
        proved that the OAuth setup is working
        """
        # We can create an instance of an endpoint resource class, and use it to fetch details
        access_token = self.get_token()
        api = AppointmentEndpoint(access_token)
        # Grab the first doctor from the list; normally this would be the whole practice group, but your hackathon
        # account probably only has one doctor in it.
        print(datetime.now().strftime("%Y-%m-%d"))
        return (api.list(date = datetime.now().strftime("%Y-%m-%d")))

    def get_context_data(self, **kwargs):
        # print(kwargs, kwargs['flag'])
        # print(self.request.session['user_id'])
        kwargs = super(CheckAppointments, self).get_context_data(**kwargs)
        
        # Hit the API using one of the endpoints just to prove that we can
        # If this works, then your oAuth setup is working correctly.
        appnt = self.appointment_api_request()
        appointment = []
        
        for app in appnt:
            # print(app)
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
            app['scheduled_time'] = date_parser.parse(app['scheduled_time'])

            appointment.append(app)
        
        if 'flag' in kwargs:
            return appointment

        filtered_Data = self.filter(appointment, self.request.session['user_id'])
        print(filtered_Data)
        if not filtered_Data:
            kwargs['appointment'] = None
        else: kwargs['appointment'] =  filtered_Data                            #self.filter(appnt, self.request.session['user_id'])

        # print(kwargs['doctor'])
        kwargs['patient_queue'] =  len(Appointments.objects.filter(Q(status='Arrived') | Q(status='In Session')))
        return kwargs

    def update_appointment_status(self, id, data, partial = True):
        access_token = self.get_token()
        api = AppointmentEndpoint(access_token)
        api.update(id, data, partial)
    
    def filter(self, appointments, patient_id):
        data = []
        # print("AAP:", appointments, patient_id)
        for appt in appointments:
            if appt['patient'] == patient_id:
                data.append(appt)
        return data

    

    



class PatientDetails(DoctorWelcome, TemplateView):
    """docstring for ClassName"""
    
    template_name = 'appointments.html'

    

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
       

    
class ScheduledAppointments(DoctorWelcome, TemplateView):
    template_name = 'schedule.html'

    def get_patients(self):
        appointments = CheckAppointments().get_context_data(flag = True)
        patients = PatientDetails()
        patient_data = []
        arrived_patient_data = []
        for appointment in appointments:
            # print(appointment)
            patient = patients.get_patient(appointment['patient'])
            patient_data.append({'id': appointment['id'] ,'name' : patient['first_name'], 'surname' : patient['last_name'], 'appointment_time': appointment['scheduled_time'], 'status' : appointment['status'] })
        
        return patient_data, arrived_patient_data

    def get_context_data(self, **kwargs):
        kwargs = super(ScheduledAppointments, self).get_context_data(**kwargs)
        # Hit the API using one of the endpoints just to prove that we can
        # If this works, then your oAuth setup is working correctly.
        patients, checkedin = self.get_patients()

        kwargs['schedule'] = patients
        kwargs['checkedin'] = checkedin
        awt = get_average_wait_time()
        if awt:
            print("awt", awt)
            kwargs['average_wait_time'] = awt
        # kwargs['schedule'] = Appointments.objects.all()
        print(kwargs['doctor'])
        return kwargs









def patient_checkin(request):
    # if this is a POST request we need to process the form data
    doctor = DoctorWelcome().get_context_data()
    
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
            elif status == '3':
                return render(request, 'checkin.html', {'form': form, 'doctor': doctor['doctor'], 'error' : 'Please check the details. No User Found.'}) 
                


    # if a GET (or any other method) we'll create a blank form
    else:
        form = CheckinForm()
    
    return render(request, 'checkin.html', {'form': form, 'doctor': doctor['doctor']})

# Function to check if Patient is valid:

def check_patient_details(request, patient_list, fname, lname, dob):
    # print(str(fname), lname, str(dob))
    for idx, patient in enumerate(patient_list):
        # print("Patient details:")
        # print(patient['first_name'], patient['last_name'], patient['date_of_birth'])
        if patient['first_name'] == fname and patient['last_name'] == lname and patient['date_of_birth'] == str(dob):
            request.session['user_id'] = patient['id']
            if patient['address'] and patient['cell_phone'] and patient['email']:
                # print("User found.")
                return ('1', {'address' : patient['address'], 'email' : patient['email'], 'phone' : patient['cell_phone']})
            else:
                return ('0', {})
    else:
        return ('3', {})
            



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

    doctor = DoctorWelcome().get_context_data()
    return render(request, 'updateinfo.html', {'form': form, 'doctor': doctor['doctor']})



def arrived(request, appid):
        if request.method == 'POST':
            # appointment_id =  request.POST.get("appid", "")
            print("appointment id:", appid)
            app = CheckAppointments()
            app.update_appointment_status(appid, {'status' : 'Arrived'})
            appointment_obj =  Appointments.objects.get(appointment_id = appid)
            appointment_obj.status = "Arrived"
            appointment_obj.arrival_time = get_local_datetime(request)
            appointment_obj.reference_time = get_local_datetime(request)
            print(appointment_obj.reference_time)
            appointment_obj.save()
            return redirect('/appointment/')





def get_local_datetime(request):
    user_timezone = request.COOKIES.get('tzname_from_user', 'UTC')
    return datetime.now(pytz.timezone(user_timezone))

def see_patient(request, appid):
    print("See Patient", appid)
    app = CheckAppointments()
    app.update_appointment_status(appid, {'status' : 'In Session'})
    appointment_obj =  Appointments.objects.get(appointment_id = appid)
    appointment_obj.status = "In Session"
    update_wait_time(request)

    return redirect('/schedule/')

def appointment_complete(request, app_id):
    print("Complete:", app_id)
    app = CheckAppointments()
    app.update_appointment_status(app_id, {'status' : 'Complete'})
    appointment_obj = Appointments.objects.get(appointment_id = app_id)
    appointment_obj.status = "Complete" 
    appointment_obj.save()
    resume_time(request)
    return redirect('/schedule/')


def update_wait_time(request):
    curr_appointments = Appointments.objects.all()
    curr_time = get_local_datetime(request)
    print("Curr time:", curr_time)
    for curr_app in curr_appointments:
        if curr_app.status != 'Complete' and curr_app.status == 'Arrived':
            print("Ref time", curr_app.reference_time)
            wait_time =  (curr_time - curr_app.reference_time)   
            print("Waiting:", wait_time)
            if curr_app.time_waited:
                curr_app.time_waited += wait_time
            else:
                curr_app.time_waited = wait_time
            curr_app.save()
            print(curr_app.appointment_id, curr_app.time_waited)

def resume_time(request):
    curr_appointments = Appointments.objects.all()
    curr_time = get_local_datetime(request)
    print("Curr time:", curr_time)
    for curr_app in curr_appointments:
        print(curr_app.appointment_id, curr_app.status, curr_app.time_waited)
        if curr_app.status != 'Complete':
            curr_app.reference_time = curr_time
            curr_app.save()


def get_average_wait_time():

    completed_appointments = Appointments.objects.filter(
        (Q(status='Complete') | Q(status='In Session')))
    
    if not completed_appointments:
        return None

    completed_appointments = [appointment.time_waited for appointment in completed_appointments]

    print(completed_appointments)
    avg = sum(completed_appointments, timedelta()) / len(completed_appointments)
    avg = str(avg).split('.')[0]  # remove fractions smaller than a second from timedelta object

    print("avg time:", avg)
    return avg

    
# def create_appointment(request): #84192274
#     data = {'patient': 84192274, 'scheduled_time': datetime.datetime.now().isoformat()}
#     App = CheckAppointments().

#     return render(request, 'create_appointment.html')