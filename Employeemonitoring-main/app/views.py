from django.shortcuts import render
from matplotlib.style import use

from .models import AttendanceLogs, Board, Employee, Meeting, Monitoring, MonitoringDetails, Organization, OrganizationNews, PowerMonitoring, Project, Project_Employee_Linker, ScreenShotsMonitoring, Task, WorkProductivityDataset, Leaves
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse

import math
import random
#from password_generator import PasswordGenerator
import uuid
import datetime
import json


from fuzzywuzzy import fuzz
from fuzzywuzzy import process

import plotly.express as px
from plotly.offline import plot
import plotly.graph_objs as go
import pandas as pd
import secrets
import string

def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for i in range(length))
    return password



#############################################################################################################################
#index page
def index(request):
    return render(request, 'index.html')

#login of organization
def org_login(request):
    if request.method == "POST":
        o_email = request.POST['o_email']
        o_pass = request.POST['o_pass']
        org_details = Organization.objects.filter(o_email=o_email, o_password=o_pass).values()
        if org_details:
            request.session['logged_in'] = True
            request.session['o_email'] = org_details[0]["o_email"]
            request.session['o_id'] = org_details[0]["id"]
            request.session['o_name'] = org_details[0]["o_name"]
            request.session['u_type'] = "org"
            return HttpResponseRedirect('/org_index')
        else:
            return render(request, 'OrgLogin.html', {'details': "0"})
    else:
        return render(request, 'OrgLogin.html')

#login of employee
def user_login(request):
    if request.method == "POST":
        e_email = request.POST['e_email']
        e_pass = request.POST['e_pass']
        user_details = Employee.objects.filter(e_email=e_email, e_password=e_pass).values()
        if user_details:
            request.session['logged_in'] = True
            request.session['u_email'] = user_details[0]["e_email"]
            request.session['u_id'] = user_details[0]["id"]
            request.session['u_name'] = user_details[0]["e_name"]
            request.session['u_oid'] = user_details[0]["o_id_id"]
            request.session['u_type'] = "emp"
            return HttpResponseRedirect('/user_index')
        else:
            return render(request, 'EmpLogin.html', {'msg': "0"})
    else:
        return render(request, 'EmpLogin.html')

#organization registeration
def org_register(request):
    if request.method == "POST":
        o_name = request.POST['org_name']
        o_email = request.POST['o_email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        contact_no = request.POST['contact_no']
        website = request.POST['website']
        o_address = request.POST['o_address']
        if password1 == password2:
            otp = generateOTP()
            request.session['tempOTP'] = otp
            subject = 'MyRemoteDesk - OTP Verification'
            message = f'Hi {o_name}, thank you for registering in MyRemoteDesk . Your One Time Password (OTP) for verfication is {otp}'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [o_email, ]
            send_mail(subject, message, email_from, recipient_list)
            request.session['tempOrg_name'] = o_name
            request.session['tempOrg_email'] = o_email
            request.session['tempPassword'] = password2
            request.session['tempContact_no'] = contact_no
            request.session['tempWebsite'] = website
            request.session['tempO_address'] = o_address
            return HttpResponseRedirect('/VerifyEmail')
        else:
            messages.error("Password not matched!")
    else:
        return render(request, 'OrgRegister.html')




#generate
def generateOTP():
    digits = "0123456789"
    OTP = ""
    for i in range(5):
        OTP += digits[math.floor(random.random() * 10)]
    return OTP


#verifying email for registration

def verifyEmail(request):
    if request.method == 'POST':
        theOTP = request.POST.get('eotp')
        mOTP = request.session.get('tempOTP')

        if not theOTP or not mOTP:
            messages.error(request, 'Invalid OTP or session expired.')
            return render(request, 'verifyOTP.html')

        if theOTP == mOTP:
            myDB_o_name = request.session.get('tempOrg_name')
            myDB_o_email = request.session.get('tempOrg_email')
            myDB_password = request.session.get('tempPassword')
            myDB_contact_no = request.session.get('tempContact_no')
            myDB_website = request.session.get('tempWebsite')
            myDB_o_address = request.session.get('tempO_address')

            if all([myDB_o_name, myDB_o_email, myDB_password, myDB_contact_no, myDB_website, myDB_o_address]):
                try:
                    obj = Organization.objects.create(
                        o_name=myDB_o_name,
                        o_email=myDB_o_email,
                        o_password=myDB_password,
                        o_contact=myDB_contact_no,
                        o_website=myDB_website,
                        o_address=myDB_o_address
                    )
                    obj.save()

                    # Clear session data
                    for key in list(request.session.keys()):
                        del request.session[key]

                    messages.success(request, "You are successfully registered")
                    return HttpResponseRedirect('/LoginOrg')

                except Exception as e:
                    # Clear session data
                    for key in list(request.session.keys()):
                        del request.session[key]

                    messages.error(request, f"An error occurred: {str(e)}")
                    return render(request, 'OrgLogin.html', {'details': "Error Occurred"})

            else:
                messages.error(request, "Session data missing, please try again.")
                return HttpResponseRedirect('/OrgRegister')

        else:
            messages.error(request, 'OTP does not match!')
            return render(request, 'verifyOTP.html')

    # Handle the GET request or any unexpected situation
    return render(request, 'verifyOTP.html')

#contact

def contact(request):
    if request.method == 'POST':
        cname = request.POST['cname']
        cemail = request.POST['cemail']
        cquery = request.POST['cquery']
        subject = 'MyRemoteDesk - New Enquiry'
        message = f'Name : {cname}, Email : {cemail}, Query : {cquery}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [""]
        send_mail(subject, message, email_from, recipient_list)
        send_mail(subject, "YOUR QUERY WILL BE PROCESSED! WITHIN 24 HOURS", email_from, [cemail])
        messages.success(request, "Your Query has been recorded.")
        msg = "Your Query has been recorded."
        return render(request, 'contact.html', {"msg" : msg})
    return render(request, 'contact.html')


#faq

def faq(request):
    return render(request, 'faq.html')

#   Forget password for  organization in index page
def org_forgot_password(request):
    if request.method == 'POST':
        o_email = request.POST['o_email']
        request.session['tempfpOrgEmail'] = o_email
        org_details = Organization.objects.filter(o_email=o_email).values()
        if org_details:
            otp = generateOTP()
            request.session['tempfpOrgOTP'] = otp
            subject = 'MyRemoteDesk - OTP Verification for Forgot Password'
            message = f'Hi {o_email}, Your One Time Password (OTP) for forgot password is is {otp}'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [o_email, ]
            send_mail(subject, message, email_from, recipient_list)
            return HttpResponseRedirect('/org-forgot-password-otp-verify')
        else:
            return render(request, 'Org_fp.html', {'msg': "0"})
    else:
        return render(request, 'Org_fp.html')

# verify Email using otp for organization in index page
def org_forgot_password_otp_verify(request):
    if request.method == 'POST':
        fp_org_otp = request.POST['fp_org_otp']
        tempOrgFpOTP = request.session['tempfpOrgOTP']
        if(fp_org_otp == tempOrgFpOTP):
            return HttpResponseRedirect('/org-forgot-password-change-pass')
        else:
            return render(request, 'OrgFpVerifyOTP.html', {'msg': "0"})
    else:
        return render(request, 'OrgFpVerifyOTP.html')

# change password for organization after verifyinng the otp in index page
def org_forgot_password_change_password(request):
    if request.method == 'POST':
        tempOrgFpEmail = request.session['tempfpOrgEmail']
        pwd1 = request.POST['pwd1']
        pwd2 = request.POST['pwd2']
        if(pwd1 == pwd2):
            org_details = Organization.objects.filter(o_email=tempOrgFpEmail).update(o_password=pwd1)
            if org_details:
                subject = 'MyRemoteDesk - Password was Changed'
                message = f'Hi, Your Password was changed!'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [tempOrgFpEmail]
                send_mail(subject, message, email_from, recipient_list)
                return render(request, 'OrgFpChangePass.html', {'msg': '10'})
            else:
                return render(request, 'OrgFpChangePass.html', {'msg': '11'})
        else:
            return render(request, 'OrgFpChangePass.html', {'msg': "2"})
    else:
        return render(request, 'OrgFpChangePass.html')


# change password for employee in index page
def user_forgot_password(request):
    if request.method == 'POST':
        e_email = request.POST['e_email']
        request.session['tempfpEmpEmail'] = e_email
        emp_details = Employee.objects.filter(e_email=e_email).values()
        if emp_details:
            otp = generateOTP()
            request.session['tempfpEmpOTP'] = otp
            subject = 'MyRemoteDesk - OTP Verification for Forgot Password'
            message = f'Hi {e_email}, Your One Time Password (OTP) for forgot password is is {otp}'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [e_email, ]
            send_mail(subject, message, email_from, recipient_list)
            return HttpResponseRedirect('/user-forgot-password-otp-verify')
        else:
            return render(request, 'Emp_fp.html', {'msg': "0"})
    else:
        return render(request, 'Emp_fp.html')

#verifying the otp for password change for employee in index page
def user_forgot_password_otp_verify(request):
    if request.method == 'POST':
        fp_emp_otp = request.POST['fp_emp_otp']
        tempEmpFpOTP = request.session['tempfpEmpOTP']
        if(fp_emp_otp == tempEmpFpOTP):
            return HttpResponseRedirect('/user-forgot-password-change-pass')
        else:
            return render(request, 'EmpFpVerifyOTP.html', {'msg': "0"})
    else:
        return render(request, 'EmpFpVerifyOTP.html')

#change password for employee after the verifying for employee in index page
def user_forgot_password_change_password(request):
    if request.method == 'POST':
        tempEmpFpEmail = request.session['tempfpEmpEmail']
        pwd1 = request.POST['pwd1']
        pwd2 = request.POST['pwd2']
        if(pwd1 == pwd2):
            emp_details = Employee.objects.filter(e_email=tempEmpFpEmail).update(e_password=pwd1)
            if emp_details:
                subject = 'MyRemoteDesk - Password was Changed'
                message = f'Hi, Your Password was changed!'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [tempEmpFpEmail]
                send_mail(subject, message, email_from, recipient_list)
                return render(request, 'EmpFpChangePass.html', {'msg': '10'})
            else:
                return render(request, 'EmpFpChangePass.html', {'msg': '11'})
        else:
            return render(request, 'EmpFpChangePass.html', {'msg': "2"})
    else:
        return render(request, 'EmpFpChangePass.html')


###############################################################################################################################

#session login requreired for user and organization
def org_login_required(function):
    def wrapper(request, *args, **kw):
        if 'logged_in' in request.session:
            if request.session['u_type'] == 'org':
                return function(request, *args, **kw)
            else:
                messages.error(request, "You don't have privilege to access this page!")
                return HttpResponseRedirect('/')
        else:
            messages.error(request, "Logout Request/ Unauthorized Request, Please login!")
            return HttpResponseRedirect('/LoginOrg')
    return wrapper

def user_login_required(function):
    def wrapper(request, *args, **kw):
        if 'logged_in' in request.session:
            if request.session['u_type'] == 'emp':
                return function(request, *args, **kw)
            else:
                messages.error(request, "You don't have privilege to access this page!")
                return HttpResponseRedirect('/')
        else:
            messages.error(request, "Logout Request / Unauthorized Request, Please login!")
            return HttpResponseRedirect('/LoginUser')
    return wrapper

###################################################################################################################################################
#organization login
@org_login_required
def org_index(request):
    return render(request,'OrgIndex.html')


#########  Employeee options ##################### 
# add employee to organization
@org_login_required
def add_emp(request):
    if request.method == 'POST':
        o_id = request.session['o_id']
        e_name = request.POST['e_name']
        e_email = request.POST['e_email']
        e_password = generate_password()
        e_gender = request.POST['e_gender']
        e_contact = request.POST['e_contact']
        e_address = request.POST['e_address']
        empObj = Employee.objects.create(e_name=e_name, e_email=e_email, e_password=e_password,e_contact=e_contact, e_gender=e_gender, e_address=e_address, o_id_id=o_id)
        if empObj:
            subject = 'MyRemoteDesk - Login Info'
            org_name = request.session['o_name']
            message = f'\nName : {e_name}, \n Email : {e_email}, \n Password : {e_password} \n Organization : {org_name}, \n FROM - MyRemoteDesk \n pramod,siddappa'
            email_from = settings.EMAIL_HOST_USER
            send_mail(subject, message, email_from, [e_email])
            messages.success(request, "Employee was added successfully!")
            return HttpResponseRedirect('/create-emp')
        else:
            messages.error(request, "Some error was occurred!")
            return HttpResponseRedirect('/create-emp')
    return render(request, 'AddEmp.html')


#view employee list
@org_login_required
def read_emp(request):
    if request.method == 'GET':
        o_id = request.session['o_id']
        emp_details = Employee.objects.filter(o_id_id=o_id).values()
        return render(request, 'ViewEmp.html', {"msg": emp_details})

# in above page for view option
@org_login_required
def view_emp(request,eid):
    if request.method == 'GET':
        o_id = request.session['o_id']
        emp_details = Employee.objects.filter(o_id_id=o_id, id=eid).first()
        count_no_of_total_tasks = Task.objects.filter(o_id_id=o_id, e_id_id=eid).count()
        count_no_of_completed_tasks = Task.objects.filter(o_id_id=o_id, e_id_id=eid, t_status="completed").count()
        count_no_of_pending_tasks = count_no_of_total_tasks - count_no_of_completed_tasks
        pel_details = Project_Employee_Linker.objects.filter(o_id_id=o_id, e_id_id=eid).values_list('p_id_id', flat=True)
        project_details = Project.objects.filter(id__in=pel_details).values()
        return render(request, 'EmpDetails.html', {"msg": emp_details, "msg1": count_no_of_total_tasks, "msg2": count_no_of_completed_tasks, "msg3": count_no_of_pending_tasks, "msg4": project_details})

# in above page  for update option 
@org_login_required
def update_emp(request, eid):
    try:
        emp_detail = Employee.objects.filter(id=eid,o_id_id=request.session['o_id'])
        if request.method == "POST":
            e_name = request.POST['e_name']
            e_email = request.POST['e_email']
            e_gender = request.POST['e_gender']
            e_contact = request.POST['e_contact']
            e_address = request.POST['e_address']
            emp_detail = Employee.objects.get(id=eid)
            emp_detail.e_name = e_name
            emp_detail.e_email = e_email
            emp_detail.e_gender = e_gender
            emp_detail.e_contact = e_contact
            emp_detail.e_address = e_address
            emp_detail.save()
            if emp_detail:
                messages.success(request, "Employee Data was updated successfully!")
                return HttpResponseRedirect('/read-emp')
            else:
                messages.error(request, "Some Error was occurred!")
                return HttpResponseRedirect('/read-emp')
        return render(request, 'UpdateEmp.html', {'emp_detail':emp_detail[0]})
    except:
        messages.error(request, "Some Error was occurred!")
        return HttpResponseRedirect('/read-emp')

# in above page delete  option 
@org_login_required
def del_emp(request, eid):
    try:
        emp_detail = Employee.objects.filter(id=eid,o_id_id=request.session['o_id']).delete()
        if emp_detail:
            messages.success(request, "Employee was deleted successfully!")
            return HttpResponseRedirect('/read-emp')
        else:
            messages.error(request, "Some Error was occurred!")
            return HttpResponseRedirect('/read-emp')
    except:
        messages.error(request, "Some Error was occurred!")
        return HttpResponseRedirect('/read-emp')



#leaves list of employees
@org_login_required
def org_emp_leave_views(request):
    o_id = request.session['o_id']
    LeaveObj = Leaves.objects.filter(o_id_id=o_id,l_status="Assigned").all()
    return render(request, 'OrgEmpLeavesTbl.html' , {"leaves": LeaveObj})

# approval of leave
@org_login_required
def org_emp_leave_approval(request, pk):
    LeaveInd = Leaves.objects.get(id=pk, o_id_id=request.session['o_id'])
    if request.method == 'POST':
        LeaveInd.l_status = request.POST['l_status']
        LeaveInd.save()
        if LeaveInd:
            messages.success(request, "Leave Request Approved Successfully")
            return HttpResponseRedirect('/emp-leaves')
        else:
            messages.error(request, "Leave Request Not Approved Successfully")
            return HttpResponseRedirect('/emp-leaves')


##################################################


############## Projects ######################

#create project
@org_login_required
def create_proj(request):
    if request.method == 'POST':
        p_name = request.POST['p_name']
        p_desc = request.POST['p_desc']
        projCheck = Project.objects.filter(p_name=p_name, o_id_id=request.session['o_id'])
        if projCheck:
            messages.error(request, "Project already exists!")
            return HttpResponseRedirect('/create-proj')
        else:
            projObj = Project.objects.create(
                p_name=p_name, p_desc=p_desc, o_id_id=request.session['o_id'])
            if projObj:
                messages.success(request, "Project added successfully!")
                return HttpResponseRedirect('/create-proj')
            else:
                messages.error(request, "Some Error was occurred!")
                return HttpResponseRedirect('/create-proj')
    return render(request, 'OrgCreateProject.html')

#view project
@org_login_required
def read_proj(request):
    if request.method == 'GET':
        project_details = Project.objects.filter(o_id_id=request.session['o_id']).values()
        return render(request, 'ViewProjects.html', {"msg": project_details})

#under view paage to view the tasks
@org_login_required
def projectwise_task(request,pid):
    if request.method == 'GET':
        o_id = request.session['o_id']
        project_details = Project.objects.filter(o_id_id=o_id, id=pid).all()
        tasks = Task.objects.filter(o_id_id=o_id, p_id_id=pid).all()
        count_no_of_total_tasks = Task.objects.filter(o_id_id=o_id, p_id_id=pid).count()
        count_no_of_completed_tasks = Task.objects.filter(o_id_id=o_id, p_id_id=pid, t_status="completed").count()
        count_no_of_pending_tasks = count_no_of_total_tasks - count_no_of_completed_tasks
        if tasks:
            tasklist = []
            for task in tasks:
                Dict = {}
                Dict["Task"] = task.t_name
                Dict["Start"] = task.t_assign_date
                Dict["Finish"] = task.t_deadline_date
                Dict["Resource"] = task.t_priority
                tasklist.append(Dict)
            df = pd.DataFrame(tasklist)
            fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Resource")
            fig.update_yaxes(autorange="reversed")
            plot_div = plot(fig, output_type='div')
            context = {"project_details": project_details, 'plot_div': plot_div, 'task_total': count_no_of_total_tasks, 'task_completed': count_no_of_completed_tasks, 'task_pending': count_no_of_pending_tasks }
            return render(request, 'ViewProjectwiseTasks.html', context)
        else:
            return render(request, 'ViewProjectwiseTasks.html')


# delete task under view page
@org_login_required  
def delete_task(request, pk):
    try:
        tasks = Task.objects.get(id=pk, o_id_id=request.session['o_id']).delete()
        if tasks:
            messages.success(request, "Task was deleted successfully!")
            return HttpResponseRedirect('/read-task')
        else:
            messages.error(request, "Some Error was occurred!")
            return HttpResponseRedirect('/read-task')
    except:
        messages.error(request, "Some Error was occurred!")
        return HttpResponseRedirect('/read-task')

#under the view page delete projects
@org_login_required
def del_proj(request, pid):
    try:
        project_detail = Project.objects.filter(id=pid,o_id_id=request.session['o_id']).delete()
        if project_detail:
            messages.success(request, "Project was deleted successfully!")
            return HttpResponseRedirect('/read-proj')
        else:
            messages.error(request, "Some Error was occurred!")
            return HttpResponseRedirect('/read-proj')
    except:
        messages.error(request, "Some Error was occurred!")
        return HttpResponseRedirect('/read-proj')

#assign project
@org_login_required
def assign_proj_emp(request):
    o_id = request.session['o_id']
    projAssign_details = Project_Employee_Linker.objects.filter(o_id_id=o_id).prefetch_related('p_id_id','e_id_id')        
    project_details = Project.objects.filter(o_id_id=o_id).values()
    emp_details = Employee.objects.filter(o_id_id=o_id).values()
    if request.method == 'POST':
        p_id = request.POST['p_id']
        e_id = request.POST['e_id']
        projAssignCheck = Project_Employee_Linker.objects.filter(p_id_id=p_id, e_id_id=e_id, o_id_id=o_id)
        if projAssignCheck:
            messages.error(request, "Project already exists!")
            return HttpResponseRedirect('/assign-proj')
        else:
            projAssignCheckObj = Project_Employee_Linker.objects.create(e_id_id = e_id, o_id_id = o_id, p_id_id = p_id)
            if projAssignCheckObj:
                user_details = Employee.objects.filter(id=e_id,o_id_id=o_id).values()
                s_email = user_details[0]["e_email"]
                s_name = user_details[0]["e_name"]
                project_details = Project.objects.filter(o_id_id=o_id,id=p_id).values()
                s_p_name = project_details[0]["p_name"]
                if user_details and project_details:
                    subject = 'MyRemoteDesk - Project was Assigned to you'
                    message = f'Hi, {s_name} You are asssigned to project {s_p_name} Check on MyRemoteDesk !'
                    email_from = settings.EMAIL_HOST_USER
                    recipient_list = [s_email]
                    send_mail(subject, message, email_from, recipient_list)
                messages.success(request, "Employee was Successfully Assigned with Project!")
                return HttpResponseRedirect('/assign-proj')
            else:
                messages.error(request, "Error was occurred!")
                return HttpResponseRedirect('/assign-proj')
    return render(request, 'AssignProjEmp.html', {'msg1':project_details,'msg2':emp_details,'msg3':projAssign_details})

#unassign project
@org_login_required
def select_unassign(request):
    o_id = request.session['o_id']
    project_details = Project.objects.filter(o_id_id=o_id).values()
    return render(request, 'unassign.html', {"msg": project_details})

# unassign employee to project
@org_login_required
def unassign_employee(request):
    o_id = request.session['o_id']
    pid = request.POST['p_id']
    pname = Project.objects.filter(id=pid).values_list('p_name',flat=True)[0]
    proj_emp_ids = Project_Employee_Linker.objects.filter(o_id_id=o_id, p_id_id=pid).values_list('e_id_id', flat=True)
    emp_details = [list(Employee.objects.filter(id=eid).values())[0] for eid in proj_emp_ids]
    return render(request, 'unassignemp.html', {"msg": emp_details, 'pname':pname, 'pid':pid})

@org_login_required
def unassign_emp(request, eid):
    if request.method == 'POST':
        o_id = request.session['o_id']
        pid = request.POST['p_id']
        emp_detail = Project_Employee_Linker.objects.filter(o_id_id=o_id, e_id_id=eid, p_id_id=pid).delete()
        return redirect('/unassign_employee')

###########################################

########## Board option ###################

#create board
@org_login_required
def create_board(request):
    if request.method == 'POST':
        o_id = request.session['o_id']
        b_name = request.POST['b_name']
        boardCheck = Board.objects.filter(b_name=b_name, o_id_id=o_id)
        if boardCheck:
            messages.error(request, "Board already exists!")
            return HttpResponseRedirect('/create-board')
        else:
            boardObj = Board.objects.create(b_name=b_name, o_id_id=o_id)
            if boardObj:
                messages.success(request, "Board created successfully!")
                return HttpResponseRedirect('/create-board')
            else:
                messages.error(request, "Some error was occurred!")
                return HttpResponseRedirect('/create-board')
    return render(request, 'AddBoard.html')

#view board
@org_login_required
def read_boards(request):
    if request.method == 'GET':
        board_details = Board.objects.filter(o_id_id=request.session['o_id']).values()
        return render(request, 'ViewBoards.html', {"msg": board_details})

# view boardwise tasks
@org_login_required
def boardwise_task(request,bid):
    if request.method == 'GET':
        o_id = request.session['o_id']
        board_details = Board.objects.filter(o_id_id=o_id,id=bid).all()
        context = {"board_details": board_details}
        return render(request, 'ViewBoardwiseTasks.html', context)

# delete board
@org_login_required
def del_board(request, bid):
    try:
        board_detail = Board.objects.filter(id=bid,o_id_id=request.session['o_id']).delete()
        if board_detail:
            messages.success(request, "Board was deleted successfully!")
            return HttpResponseRedirect('/read-boards')
        else:
            messages.error(request, "Some Error was occurred!")
            return HttpResponseRedirect('/read-boards')
    except:
        messages.error(request, "Some Error was occurred!")
        return HttpResponseRedirect('/read-boards')

############################################

########## Task option #############################

#task overview
@org_login_required
def overview_task(request):
    o_id = request.session['o_id']
    board_details = Board.objects.filter(o_id_id=o_id).all()
    org_board_names = list(Board.objects.filter(o_id_id=o_id).values_list('b_name',flat=True))
    if request.method == "POST":
        priority = request.POST['t_priority_filter']
        status = request.POST['t_status_filter']
        context = {"board_details": board_details, 'org_board_names':org_board_names, 'priority':priority, 'status':status}
        return render(request, 'OverviewTasks.html', context)
    else:      
        board_details = Board.objects.filter(o_id_id=o_id).all()
        context = {"board_details": board_details,'org_board_names':org_board_names, 'priority':'any', 'status':'any'}
        return render(request, 'OverviewTasks.html', context)

#create task
@org_login_required
def create_task(request):
    o_id = request.session['o_id']
    boards = Board.objects.filter(o_id_id=o_id).values()
    projects = Project.objects.filter(o_id_id=o_id).values()
    employees = Employee.objects.filter(o_id_id=o_id).values()
    context = {"boards": boards, "projects": projects, "employees": employees}
    if request.method == 'POST':
        t_name = request.POST['t_name']
        t_desc = request.POST['t_desc']
        t_assign_date = request.POST['t_assign_date']
        t_deadline_date = request.POST['t_deadline_date']
        t_status = "todo"
        t_priority = request.POST['t_priority']
        b_id = request.POST['b_id']
        p_id = request.POST['p_id']
        e_id = request.POST['e_id']
        taskObj = Task.objects.create(t_name=t_name, t_desc=t_desc, t_assign_date=t_assign_date, t_deadline_date=t_deadline_date,
                                      t_status=t_status, t_priority=t_priority, o_id_id=o_id, b_id_id=b_id, p_id_id=p_id, e_id_id=e_id)
        if taskObj:
            empDetails = Employee.objects.filter(id=e_id, o_id_id=o_id).values()
            subject = 'MyRemoteDesk - New Task Created for you'
            message = f'Hi {empDetails[0]["e_name"]} , Your organization as created a new task : {t_name} , description : {t_desc}, priority : {t_priority} and deadline for task is : {t_deadline_date}, Login in your account to get more information. From: MyRemoteDesk. '
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [empDetails[0]["e_email"], ]
            send_mail(subject, message, email_from, recipient_list)
            messages.success(request, "Task was created successfully!")
            return HttpResponseRedirect('/create-task')
        else:
            messages.error(request, "Some Error was occurred!")
            return HttpResponseRedirect('/create-task')
    return render(request, 'CreateTask.html', context)

#view and edit task
@org_login_required
def read_tasks(request):
    o_id = request.session['o_id']
    board_details = Board.objects.filter(o_id_id=o_id).all()
    if request.method == 'GET':
        return render(request, 'ViewTasks.html', {"board_details": board_details})
    else:
        return render(request, 'ViewTasks.html')

######################################################

############ Meeting option #########################

#create meeting
@org_login_required
def create_meet(request):
    o_id = request.session['o_id']
    project_details = Project.objects.filter(o_id_id=o_id).values()
    if request.method == 'POST':
        p_id = request.POST['p_id']
        m_name = request.POST['m_name']
        m_desc = request.POST['m_desc']
        start_date = request.POST['start_date']
        stop_date = request.POST['stop_date']
        start_time = request.POST['start_time']
        stop_time = request.POST['stop_time']
        m_uuid = uuid.uuid1()
        meetingObj = Meeting.objects.create(m_name = m_name, m_desc = m_desc, m_uuid = m_uuid, m_start_date = start_date, m_start_time = start_time, m_stop_date = stop_date, m_stop_time = stop_time, p_id_id = p_id, o_id_id = o_id)
        if meetingObj:
            pel_details = Project_Employee_Linker.objects.filter(o_id_id=o_id,p_id_id=p_id).values_list('e_id_id', flat=True)
            user_details = Employee.objects.filter(id__in=pel_details).values()
            if user_details:
                for ud in user_details:
                    subject = 'MyRemoteDesk - New Meeting'
                    s_name = ud['e_name']
                    s_email = ud['e_email']
                    message = f'Hi, {s_name} New Meeting for created for you! Details are Meeting Name :{m_name}, Meeting Description: {m_desc}, Date Time: {start_date} {start_time} Check on MyRemoteDesk !'
                    email_from = settings.EMAIL_HOST_USER
                    recipient_list = [s_email]
                    send_mail(subject, message, email_from, recipient_list)
            messages.success(request,"Meeting is created successfully!")
            return HttpResponseRedirect('/create-meet')
        else:
            messages.error(request, "Some error was occurred!")
            return HttpResponseRedirect('/create-meet')
    return render(request, 'AddMeeting.html', {'msg1':project_details})

#view meeting
@org_login_required
def read_meet(request):
    if request.method == 'GET':
        meeting_details = Meeting.objects.filter(o_id_id=request.session['o_id']).values()
        return render(request, 'ViewMeeting.html', {"msg": meeting_details})

# Edit meeting
@org_login_required
def edit_meet(request, mid):
    try:
        o_id = request.session['o_id']
        meet_details = Meeting.objects.filter(id=mid,o_id_id=o_id)
        current_pid = Meeting.objects.filter(id=mid,o_id_id=o_id).values()[0]['p_id_id']
        current_project_name = Project.objects.filter(id=current_pid,o_id_id=o_id).values()[0]['p_name']
        project_names = Project.objects.filter(o_id_id=o_id).values_list('p_name', flat=True)
        pids = Project.objects.values_list('id', flat=True)
        zipped_pid_pnames = zip(pids, project_names)
        if request.method == "POST":
            meet_name = request.POST['m_name']
            p_id = request.POST['p_id']
            start_date = request.POST['start_date']
            start_time = request.POST['start_time']
            meet_desc = request.POST['m_desc']
            meet_details = Meeting.objects.get(id=mid)
            meet_details.m_name = meet_name
            meet_details.p_id_id = p_id
            meet_details.m_start_date= start_date
            meet_details.m_start_time = start_time
            meet_details.m_desc = meet_desc
            meet_details.save()
            if meet_details:
                pel_details = Project_Employee_Linker.objects.filter(o_id_id=o_id,p_id_id=p_id).values_list('e_id_id', flat=True)
                user_details = Employee.objects.filter(id__in=pel_details).values()
                if user_details:
                    for ud in user_details:
                        subject = 'MyRemoteDesk - New Meeting'
                        s_name = ud['e_name']
                        s_email = ud['e_email']
                        message = f'Hi, {s_name} New Meeting for created for you! Details are Meeting Name :{meet_name}, Meeting Description: {meet_desc}, Date Time: {start_date} {start_time} Check on MyRemoteDesk !'
                        email_from = settings.EMAIL_HOST_USER
                        recipient_list = [s_email]
                        send_mail(subject, message, email_from, recipient_list)
                messages.success("Meeting Updated Successfully!")
                return HttpResponseRedirect('/read-meet')
            else:
                messages.error("Some error was occurred!")
                return HttpResponseRedirect('/read-meet')
        return render(request, 'UpdateMeeting.html', {'meet_details':meet_details[0], 'zipped_pid_pnames':zipped_pid_pnames, 'current_project_name':current_project_name})
    except:
        messages.error(request, "Some Error was occurred!")
        return HttpResponseRedirect('/read-meet')

# Delete meeting
@org_login_required
def del_meet(request, mid):
    try:
        meet_details = Meeting.objects.filter(id=mid, o_id_id=request.session['o_id']).delete()
        if meet_details:
            messages.success(request, "Meeting was deleted successfully!")
            return HttpResponseRedirect('/read-meet')
        else:
            messages.error(request, "Some error was occurred!")
            return HttpResponseRedirect('/read-meet')
    except:
        messages.error(request, "Some Error was occurred!")
        return HttpResponseRedirect('/read-meet')

##################################################

############## Notice option #####################

#notice overview
@org_login_required
def overview_notices(request):
    o_id = request.session['o_id']
    noticeObj = OrganizationNews.objects.filter(o_id_id=o_id).all()
    if request.method == 'GET':
        return render(request, 'OverviewNotices.html', {"notices": noticeObj})
    else:
        return render(request, 'OverviewNotices.html', {"notices": noticeObj})

#create notice
@org_login_required
def create_notice(request):
    o_id = request.session['o_id']
    if request.method == 'POST':
        on_title = request.POST['on_title']
        on_desc = request.POST['on_desc']
        noticeObj = OrganizationNews.objects.create(on_title=on_title, on_desc=on_desc, o_id_id=o_id)
        if noticeObj:
            user_details = Employee.objects.filter(o_id_id=o_id).values()
            if user_details:
                for ud in user_details:
                    subject = 'MyRemoteDesk - New Notice Published'
                    s_name = ud['e_name']
                    s_email = ud['e_email']
                    message = f'Hi, {s_name} Your Organization has published a new notice, Notice Title: {on_title} Check on MyRemoteDesk !'
                    email_from = settings.EMAIL_HOST_USER
                    recipient_list = [s_email]
                    send_mail(subject, message, email_from, recipient_list)
            messages.success(request,"Notice was created successfully!")
            return HttpResponseRedirect('/create-notice')
        else:
            messages.error(request, "Some Error was occurred!")
            return HttpResponseRedirect('/create-notice')
    return render(request, 'CreateNotice.html' )

#view notice
@org_login_required
def read_notices(request):
    o_id = request.session['o_id']
    noticeObj = OrganizationNews.objects.filter(o_id_id=o_id).values()
    return render(request, 'ViewNotices.html', {"notices": noticeObj})

# update notice
@org_login_required
def update_notice(request, pk):
    try:
        noticeObj = OrganizationNews.objects.get(id=pk,o_id_id=request.session['o_id'])
        if request.method == 'POST':
            noticeObj.on_title = request.POST['on_title']
            noticeObj.on_desc = request.POST['on_desc']
            noticeObj.save()
            if noticeObj:
                messages.success(request, "Notice was updated successfully!")
                return HttpResponseRedirect('/read-notice')
            else:
                messages.error(request, "Some Error was occurred!")
                return HttpResponseRedirect('/read-notice')
        else:
            return render(request, 'UpdateNotice.html', {"noticeObj": noticeObj })
    except:
        messages.error(request, "Some Error was occurred!")
        return HttpResponseRedirect('/read-notice')


# delete notice
@org_login_required  
def delete_notice(request, pk):
    try:
        noticeObj = OrganizationNews.objects.get(id=pk,o_id_id=request.session['o_id']).delete()
        if noticeObj:
            messages.success(request, "Notice was deleted successfully!")
            return HttpResponseRedirect('/read-notice')
        else:
            messages.error(request, "Some Error was occurred!")
            return HttpResponseRedirect('/read-notice')
    except:
        messages.error(request, "Some Error was occurred!")
        return HttpResponseRedirect('/read-notice')

###############################################


########### Report pronblem ###############

@org_login_required
def report_org(request):
    if request.method == 'POST':
        cname = request.session['o_name']
        cemail = request.session['o_email']
        ptype = request.POST['prob_type']
        cquery = request.POST['rquery']
        subject = 'MyRemoteDesk - New Enquiry'
        message = f'Name : {cname}, Email : {cemail}, Problem : {ptype}, Query : {cquery}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = ["pramodtopannavar843@gmail.com"]
        send_mail(subject, message, email_from, recipient_list)
        send_mail(subject, "Your Problem has been recorded. From: MyRemoteDesk", email_from, [cemail])
        msg = "Your Problem has been recorded."
        messages.success(request, "Your Problem has been recorded.")
        return HttpResponseRedirect('/org_report_problems')    
    return render(request, 'OrgReportProblems.html')

########## change password ##################
@org_login_required
def org_change_password(request):
    if request.method == 'POST':
        oldPwd = request.POST['oldPwd']
        newPwd = request.POST['newPwd']
        o_id = request.session['o_id']
        o_email = request.session['o_email']
        org_details = Organization.objects.filter(o_email=o_email, o_password=oldPwd, pk=o_id).update(o_password=newPwd)
        if org_details:
            subject = 'MyRemoteDesk - Password Changed'
            message = f'Hi, your password was changed successfully! From MyRemoteDesk'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [o_email, ]
            send_mail(subject, message, email_from, recipient_list)
            messages.success(request, "Password Change Successfully")
            return HttpResponseRedirect('/org_change_password')
        else:
            subject = 'MyRemoteDesk - Notifications'
            message = f'Hi, there was attempt to change your password! From MyRemoteDesk'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [o_email, ]
            send_mail(subject, message, email_from, recipient_list)
            messages.error(request, "Old Password was not matched!")
            return HttpResponseRedirect('/org_change_password')
    else:
        return render(request, 'OrgChangePass.html')



########################################################

####################################################################################################################################################
#employee login
@user_login_required
def user_index(request):
    return render(request,'EmpIndex.html')


############## Profile view ####################
@user_login_required
def user_profile(request):
    if request.method == 'GET':
        o_id = request.session['u_oid']
        e_id = request.session['u_id']
        emp_details = Employee.objects.filter(o_id_id=o_id, id=e_id).first()
        count_no_of_total_tasks = Task.objects.filter(o_id_id=o_id, e_id_id=e_id).count()
        count_no_of_completed_tasks = Task.objects.filter(o_id_id=o_id, e_id_id=e_id, t_status="completed").count()
        count_no_of_pending_tasks = count_no_of_total_tasks - count_no_of_completed_tasks
        pel_details = Project_Employee_Linker.objects.filter(o_id_id=o_id, e_id_id=e_id).values_list('p_id_id', flat=True)
        project_details = Project.objects.filter(id__in=pel_details).values()
        return render(request, 'EmpProfile.html', {"msg": emp_details, "msg1": count_no_of_total_tasks, "msg2": count_no_of_completed_tasks, "msg3": count_no_of_pending_tasks, "msg4": project_details})

############# Notice view ######################
@user_login_required
def emp_view_notices(request):
    o_id = request.session['u_oid']
    noticeObj = OrganizationNews.objects.filter(o_id_id=o_id).order_by('-id').all()
    context = {"notices": noticeObj}
    return render(request, 'EmpNotices.html', context)


############ Meeting view #######################
@user_login_required
def user_read_meets(request):
    if request.method == 'GET':
        o_id = request.session['u_oid']
        e_id = request.session['u_id']
        pel_details = Project_Employee_Linker.objects.filter(o_id_id=o_id, e_id_id=e_id).order_by('-id').values_list('p_id_id', flat=True)
        meeting_details = Meeting.objects.filter(p_id_id__in=pel_details).values()
        return render(request, 'EmpViewMeeting.html', {"msg": meeting_details})

########### Monitoring option ###################

#web and app logs
@user_login_required
def user_view_app_web(request):
    if request.method == 'POST':
        o_id = request.session['u_oid']
        e_id = request.session['u_id']
        m_date = request.POST['date_log']
        m_date_f1 = datetime.datetime.strptime(m_date, '%Y-%m-%d')
        m_date_f2 = datetime.datetime.strftime(m_date_f1, '%Y-%m-%d')
        moni_details = Monitoring.objects.filter(o_id_id=o_id, e_id_id=e_id, m_log_ts__startswith=m_date_f2).exclude(m_title="").values()
        return render(request, 'EmpViewMoniLogs.html', {"msg": moni_details})
    else:
        return render(request, 'EmpSelectMoniEmp.html')

#Detailed app logs
@user_login_required
def user_depth_view_app_web(request):
    if request.method == 'POST':
        o_id = request.session['u_oid']
        e_id = request.session['u_id']
        md_date = request.POST['date_log']
        md_date_f1 = datetime.datetime.strptime(md_date, '%Y-%m-%d')
        md_date_f2 = datetime.datetime.strftime(md_date_f1, '%Y-%#m-%#d')
        depth_moni_details = MonitoringDetails.objects.filter(o_id_id=o_id, e_id_id=e_id,  md_date__startswith=md_date_f2).exclude(md_title="").values()
        return render(request, 'EmpViewDepthMoniLogs.html', {"msg": depth_moni_details})
    else:
        return render(request, 'EmpSelectDepthMoniEmp.html')

#screenshot logs
@user_login_required
def user_ss_monitoring(request):
    if request.method == 'POST':
        o_id = request.session['u_oid']
        e_id = request.session['u_id']
        ss_date = request.POST['date_log']
        ss_date_f1 = datetime.datetime.strptime(ss_date, '%Y-%m-%d')
        ss_date_f2 = datetime.datetime.strftime(ss_date_f1, '%Y-%#m-%#d')
        ss_moni_details = ScreenShotsMonitoring.objects.filter(o_id_id=o_id, e_id_id=e_id, ssm_log_ts__startswith=ss_date_f2).values()
        return render(request, 'EmpViewSSMoniLogs.html', {"msg": ss_moni_details})
    else:
        return render(request, 'EmpSelectSSMoniEmp.html')

#power monitoring logs
@user_login_required
def user_power_monitoring(request):
    if request.method == 'POST':
        o_id = request.session['u_oid']
        e_id = request.session['u_id']
        pm_date = request.POST['date_log']
        pm_date_f1 = datetime.datetime.strptime(pm_date, '%Y-%m-%d')
        pm_date_f2 = datetime.datetime.strftime(pm_date_f1, '%Y-%#m-%#d')
        ss_power_details = PowerMonitoring.objects.filter(o_id_id=o_id, e_id_id=e_id, pm_log_ts__startswith=pm_date_f2).values()
        return render(request, 'EmpViewPowerMoniLogs.html', {"msg": ss_power_details})
    else:
        return render(request, 'EmpSelectPowerMoniEmp.html')

###################################################################

################### Productivity #######################
#check productivity
@user_login_required
def user_work_productivity_check(request):
    if request.method == 'POST':
        o_id = request.session['u_oid']
        e_id = request.session['u_id']
        m_date = request.POST['date_log']
        sum_of_emp_prod = get_work_productivity_details(o_id, e_id, m_date)
        prd_total = 0 
        unprd_total = 0
        undef_total = 0   
        for i in sum_of_emp_prod:
            if i[1]==1:
                prd_total = prd_total+int(i[2])
            if i[1]==2:
                unprd_total = unprd_total+int(i[2])
            if i[1]==3:
                undef_total = undef_total+int(i[2])
        total_time_spent = prd_total + unprd_total +undef_total
        return render(request, 'EmpViewWorkProductivity.html', {"msg": sum_of_emp_prod, "msg1": prd_total, "msg2": e_id, "msg3": m_date, "msg4": unprd_total, "msg5": undef_total, "msg6": total_time_spent})
    else:
        return render(request, 'EmpSelectWp.html')

########## Project overview ###################
#project
@user_login_required
def user_view_projects(request):
    if request.method == "GET":
        o_id = request.session['u_oid']
        e_id = request.session['u_id']
        pel_details = Project_Employee_Linker.objects.filter(o_id_id=o_id, e_id_id=e_id).values_list('p_id_id', flat=True)
        project_details = Project.objects.filter(id__in=pel_details).values()
        return render(request, 'EmpViewProj.html', {"msg": project_details})

# view project wise tasks
@user_login_required
def user_projectwise_task(request,pid):
    if request.method == 'GET':
        o_id = request.session['u_oid']
        e_id = request.session['u_id']
        project_details = Project.objects.filter(o_id_id=o_id, id=pid).all()
        tasks = Task.objects.filter(o_id_id=o_id, p_id_id=pid, e_id_id=e_id).all()
        count_no_of_total_tasks = Task.objects.filter(o_id_id=o_id, e_id_id=e_id,  p_id_id=pid).count()
        count_no_of_completed_tasks = Task.objects.filter(o_id_id=o_id, e_id_id=e_id, p_id_id=pid, t_status="completed").count()
        count_no_of_pending_tasks = count_no_of_total_tasks - count_no_of_completed_tasks
        if tasks:
            tasklist = []
            for task in tasks:
                Dict = {}
                Dict["Task"] = task.t_name
                Dict["Start"] = task.t_assign_date
                Dict["Finish"] = task.t_deadline_date
                Dict["Resource"] = task.t_priority
                tasklist.append(Dict)
            df = pd.DataFrame(tasklist)
            fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Resource")
            fig.update_yaxes(autorange="reversed")
            plot_div = plot(fig, output_type='div')
            context = {"project_details": project_details, 'plot_div': plot_div, 'task_total': count_no_of_total_tasks,
                       'task_completed': count_no_of_completed_tasks, 'task_pending': count_no_of_pending_tasks}
            return render(request, 'EmpViewProjectwiseTasks.html', context)
        else:
            return render(request, 'EmpViewProjectwiseTasks.html')

#task overview
@user_login_required
def user_overview_task(request):
    if request.method == "GET":
        o_id = request.session['u_oid']
        board_details = Board.objects.filter(o_id_id=o_id).all()
        context = {"board_details": board_details}
        return render(request, 'EmpOverviewTasks.html', context)

#tasks
@user_login_required
def emp_view_tasks(request):
    if request.method == 'GET':
        o_id = request.session['u_oid']
        board_details = Board.objects.filter(o_id_id=o_id).all()
        context = {"board_details": board_details}
        return render(request, 'EmpViewTask.html', context)

###################################################

############# Attendance and Leaves ################
#attendaance
@user_login_required
def user_view_attendance(request):
    e_id = request.session['u_id']
    if request.method=='POST':
        m_date = request.POST['date_log']
        m_date = datetime.datetime.strptime(m_date, '%Y-%m-%d')
        m_date = datetime.datetime.strftime(m_date, '%Y-%#m-%#d')
        attendance_logs = list(AttendanceLogs.objects.filter(e_id=e_id,a_date=m_date).values_list('a_date','a_ip_address','a_time_zone','a_lat','a_long'))[0]
        logged_in_time = list(AttendanceLogs.objects.filter(e_id=e_id,a_date=m_date, a_status=1).values_list('a_time'))[0][0]
        logged_out_time = list(AttendanceLogs.objects.filter(e_id=e_id,a_date=m_date, a_status=0).values_list('a_time'))[0][0]
        logged_in_time = datetime.datetime.fromtimestamp(int(logged_in_time)).strftime('%H:%M:%S')
        logged_out_time = datetime.datetime.fromtimestamp(int(logged_out_time)).strftime('%H:%M:%S')
        total_time_logged = datetime.datetime.strptime(logged_out_time,"%H:%M:%S") - datetime.datetime.strptime(logged_in_time,"%H:%M:%S")
        context = {
             'attendance_logs':list(attendance_logs), 'logged_in_time':logged_in_time, 'logged_out_time':logged_out_time, 'total_time_logged':total_time_logged
        }
        return render(request, 'UserAttendance.html', context)
    return render(request, 'UserAttendance.html')

#apply for leaves
@user_login_required
def user_apply_emp_leaves(request):
    o_id = request.session['u_oid']
    e_id = request.session['u_id']
    if request.method == 'POST':
        l_reason = request.POST['l_reason']
        l_desc = request.POST['l_desc']
        l_start_date = request.POST['l_start_date']
        l_no_of_leaves = request.POST['l_no_of_leaves']
        l_status = "Assigned"
        LeaveObj = Leaves.objects.create( l_reason=l_reason, l_desc=l_desc, l_start_date=l_start_date, l_no_of_leaves=l_no_of_leaves, l_status=l_status, o_id_id=o_id, e_id_id=e_id)
        if LeaveObj:
            messages.success(request, "Leave Request was created successfully!")
            return HttpResponseRedirect('/user-apply-emp-leaves')
        else:
            messages.error(request, "Some Error was occurred!")
            return HttpResponseRedirect('/user-apply-emp-leaves')
    else:
        return render(request, 'UserApplyEmpLeaves.html')

#view leaves
@user_login_required
def user_view_emp_leaves(request):
    o_id = request.session['u_oid']
    e_id = request.session['u_id']
    LeaveObj = Leaves.objects.filter(o_id_id=o_id, e_id_id=e_id).all()
    context = {"leaves": LeaveObj}
    return render(request, 'UserViewEmpLeaves.html' , context)

#############################################################

################## Report  problem #########################
@user_login_required
def report_emp(request):
    if request.method == 'POST':
        cname = request.session['o_name']
        cemail = request.session['o_email']
        ptype = request.POST['prob_type']
        cquery = request.POST['rquery']
        subject = 'MyRemoteDesk - New Enquiry'
        message = f'Name : {cname}, Email : {cemail}, Problem : {ptype}, Query : {cquery}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = ["pramodtopannavar843@gmail.com"]
        send_mail(subject, message, email_from, recipient_list)
        send_mail(subject, "Your Problem has been recorded. From: MyRemoteDesk", email_from, [cemail])
        msg = "Your Problem has been recorded."
        return render(request, 'EmpReportProblems.html', {"msg": msg})
    return render(request, 'EmpReportProblems.html')

################### change password #########################
@user_login_required
def user_change_password(request):
    if request.method == 'POST':
        oldPwd = request.POST['oldPwd']
        newPwd = request.POST['newPwd']
        u_id = request.session['u_id']
        u_email = request.session['u_email']
        emp_details = Employee.objects.filter(e_email=u_email, e_password=oldPwd, pk=u_id).update(e_password=newPwd)
        if emp_details:
            subject = 'MyRemoteDesk - Password Changed'
            message = f'Hi, your password was changed successfully! From MyRemoteDesk'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [u_email, ]
            send_mail(subject, message, email_from, recipient_list)
            messages.success(request,"Password Change Successfully")
            return HttpResponseRedirect('/user_change_password')
        else:
            subject = 'MyRemoteDesk - Notifications'
            message = f'Hi, there was attempt to change your password! From MyRemoteDesk'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [u_email, ]
            send_mail(subject, message, email_from, recipient_list)
            messages.error(request, "Old Password was not matched!")
            return HttpResponseRedirect('/user_change_password')
    else:
        return render(request, 'EmpChangePass.html')

####################################################################################################################################################################


def error_404_view(request, exception):
    return render(request,'404.html')

def error_500_view(request, exception):
    return render(request,'500.html')




########################################################################################################################################################








@org_login_required
def update_task(request, pk):
    try:
        o_id = request.session['o_id']
        tasks = Task.objects.get(id=pk,o_id_id=o_id)
        p_id = tasks.p_id_id
        projects_emp_link = Project_Employee_Linker.objects.filter(o_id_id=o_id, p_id_id=p_id).all()
        if request.method == 'POST':
            t_name = request.POST['t_name']
            t_desc = request.POST['t_desc']
            t_deadline_date = request.POST['t_deadline_date']
            t_priority = request.POST['t_priority']
            e_id = request.POST['e_id']
            tasks.t_name = t_name
            tasks.t_desc = t_desc
            tasks.t_deadline_date = t_deadline_date
            tasks.t_priority = t_priority
            tasks.e_id_id = e_id
            tasks.save()
            if tasks:
                empDetails = Employee.objects.filter(id=e_id, o_id_id=o_id).values()
                subject = 'MyRemoteDesk - Task Updated for you'
                message = f'Hi {empDetails[0]["e_name"]} , Your organization as updated a task : {t_name} , description : {t_desc}, priority : {t_priority} and deadline for task is : {t_deadline_date}, Login in your account to get more information. From: MyRemoteDesk. '
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [empDetails[0]["e_email"], ]
                send_mail(subject, message, email_from, recipient_list)
                messages.success(request, "Task was updated successfully!")
                return HttpResponseRedirect('/read-task')
            else:
                messages.error(request, "Some Error was occurred!")
                return HttpResponseRedirect('/read-task')
        else:
            if tasks:
                return render(request, 'UpdateTask.html', {"tasks": tasks , "projects_emp_link": projects_emp_link } )
            else:
                messages.error(request, "Some Error was occurred!")
                return HttpResponseRedirect('/read-task')
    except:
        messages.error(request, "Some Error was occurred!")
        return HttpResponseRedirect('/read-task')



@org_login_required
def get_emps_not_in_project(request, pid):
    eids = list(Project_Employee_Linker.objects.filter(p_id_id=pid,o_id_id=request.session['o_id']).values_list('e_id_id', flat=True))
    all_eids = list(Employee.objects.filter(o_id_id=request.session['o_id']).values_list('id', flat=True))
    unsassigned_emp_ids = list(set(all_eids) - set(eids)) + list(set(all_eids) - set(eids))
    unassigned_emp_enames = [Employee.objects.filter(id=eid,o_id_id=request.session['o_id']).values_list('e_name', flat=True)[0] for eid in unsassigned_emp_ids]
    e_ids_names = dict(zip(unsassigned_emp_ids, unassigned_emp_enames))
    return JsonResponse(e_ids_names)

@org_login_required
def get_emps_by_project(request, pid):
    eids = list(Project_Employee_Linker.objects.filter(p_id=pid).values_list('e_id', flat=True))
    enames = [Employee.objects.filter(id=eid).values_list('e_name', flat=True)[0] for eid in eids]
    e_ids_names = dict(zip(eids, enames))
    return JsonResponse(e_ids_names)





































@user_login_required
def emp_update_tasks(request, tid):
    o_id = request.session['u_oid']
    e_id = request.session['u_id']
    t_update_date = datetime.datetime.today().strftime('%Y-%m-%d')
    task_details = Task.objects.filter(id=tid, o_id_id=o_id, e_id_id=e_id).update(t_update_date=t_update_date, t_status="completed")
    if task_details:
        messages.success(request, "Task Mark as completed!")
        return HttpResponseRedirect('/emp-view-tasks')
    else:
        messages.error(request, "Some error was occurred!")
        return HttpResponseRedirect('/emp-view-tasks')



def get_work_productivity_details(o_id, e_id, m_date):
        md_date_f1 = datetime.datetime.strptime(m_date, '%Y-%m-%d')
        md_date_f2 = datetime.datetime.strftime(md_date_f1, '%Y-%#m-%#d')
        sum_of_emp_prod = []

        wp_ds_pr_details_unclean = list(WorkProductivityDataset.objects.filter(
            o_id_id=o_id, w_type='1').values_list('w_pds'))
        wp_ds_un_pr_details_unclean = list(WorkProductivityDataset.objects.filter(
            o_id_id=o_id, w_type='0').values_list('w_pds'))
        emp_work_data_details_unclean = list(MonitoringDetails.objects.filter(
            o_id_id=o_id, e_id_id=e_id, md_date=md_date_f2).values_list('md_title', 'md_total_time_seconds').distinct())

        wp_ds_pr_details = [
            item for x in wp_ds_pr_details_unclean for item in x]
        wp_ds_un_pr_details = [
            item for x in wp_ds_un_pr_details_unclean for item in x]
        emp_work_data_details = [
            item for x in emp_work_data_details_unclean for item in x]


        combined_wp_ds_pr_un_pr = wp_ds_pr_details + wp_ds_un_pr_details

        for emp, ti in emp_work_data_details_unclean:
            for pr in wp_ds_pr_details:
                ratio = fuzz.partial_ratio(emp, pr)
                if ratio >= 60:
                    sum_of_emp_prod.append(tuple((emp, 1, ti)))

        for emp, ti in emp_work_data_details_unclean:
            for un_pr in wp_ds_un_pr_details:
                ratio = fuzz.partial_ratio(emp, un_pr)
                if ratio >= 60:
                    sum_of_emp_prod.append(tuple((emp, 2, ti)))

        for emp, ti in emp_work_data_details_unclean:
            for combined_pr_un_pr in combined_wp_ds_pr_un_pr:
                ratio = fuzz.partial_ratio(emp, combined_pr_un_pr)
                if ratio >= 5:
                    sum_of_emp_prod.append(tuple((emp, 3, ti)))
        return sum_of_emp_prod

def get_prod_details(request, eidanddate):
    e_id = eidanddate.split('and')[0]
    m_date = eidanddate.split('and')[1]
    o_id = eidanddate.split('and')[2]
    sum_of_emp_prod = get_work_productivity_details(o_id, e_id, m_date)
    prd_total = 0 
    unprd_total = 0
    undef_total = 0   
    for i in sum_of_emp_prod:
        if i[1]==1:
            prd_total = prd_total+int(i[2])
        if i[1]==2:
            unprd_total = unprd_total+int(i[2])
        if i[1]==3:
            undef_total = undef_total+int(i[2])
    titles = ['prd_total', 'unprd_total', 'undef_total']
    values = [prd_total, unprd_total, undef_total]
    total_dict = dict(zip(titles, values))
    return JsonResponse(total_dict)

@org_login_required
def view_project_wise_employees(request):
    pids = list(Project.objects.filter(o_id_id=request.session['o_id']).values_list('id', flat=True))
    projEmps = {}
    eids = []
    eid_enames = dict(Employee.objects.filter(o_id_id=request.session['o_id']).values_list('id','e_name'))
    pnames = list(Project.objects.filter(o_id_id=2).values_list('p_name', flat=True))
    enames = []
    for pid in pids:
        e = list(Project_Employee_Linker.objects.filter(o_id_id=request.session['o_id'],p_id=pid).values_list('e_id', flat=True))
        eids.append(e)
        enames.append([eid_enames[i] for i in e])
    projEmps = dict(zip(pnames, enames))
    print(dict(zip(pnames, enames)))
    return render(request, 'ViewProjEmps.html', {'projEmps':projEmps})



def get_overall_work_productivity_details(o_id, e_id):
        sum_of_emp_prod = []

        wp_ds_pr_details_unclean = list(WorkProductivityDataset.objects.filter(
            o_id_id=o_id, w_type='1').values_list('w_pds'))
        wp_ds_un_pr_details_unclean = list(WorkProductivityDataset.objects.filter(
            o_id_id=o_id, w_type='0').values_list('w_pds'))
        emp_work_data_details_unclean = list(MonitoringDetails.objects.filter(
            o_id_id=o_id, e_id_id=e_id).values_list('md_title', 'md_total_time_seconds'))

        wp_ds_pr_details = [
            item for x in wp_ds_pr_details_unclean for item in x]
        wp_ds_un_pr_details = [
            item for x in wp_ds_un_pr_details_unclean for item in x]
        emp_work_data_details = [
            item for x in emp_work_data_details_unclean for item in x]

        combined_wp_ds_pr_un_pr = wp_ds_pr_details + wp_ds_un_pr_details

        for emp, ti in emp_work_data_details_unclean:
            for pr in wp_ds_pr_details:
                ratio = fuzz.partial_ratio(emp, pr)
                if ratio >= 70:
                    sum_of_emp_prod.append(tuple((emp, 1, ti)))

        for emp, ti in emp_work_data_details_unclean:
            for un_pr in wp_ds_un_pr_details:
                ratio = fuzz.partial_ratio(emp, un_pr)
                if ratio >= 70:
                    sum_of_emp_prod.append(tuple((emp, 2, ti)))

        for emp, ti in emp_work_data_details_unclean:
            for combined_pr_un_pr in combined_wp_ds_pr_un_pr:
                ratio = fuzz.partial_ratio(emp, combined_pr_un_pr)
                if ratio >= 5:
                    sum_of_emp_prod.append(tuple((emp, 3, ti)))
        return sum_of_emp_prod

def get_only_prod_details(oid, eid):
    o_id = oid
    e_id = eid
    sum_of_emp_prod = get_overall_work_productivity_details(o_id, e_id)
    prd_total = 0 
    unprd_total = 0
    undef_total = 0   
    for i in sum_of_emp_prod:
        if i[1]==1:
            prd_total = prd_total+int(i[2])
        if i[1]==2:
            unprd_total = unprd_total+int(i[2])
        if i[1]==3:
            undef_total = undef_total+int(i[2])
    titles = ['prd_total', 'unprd_total', 'undef_total']
    values = [prd_total, unprd_total, undef_total]
    total_dict = dict(zip(titles, values))
    return prd_total

@org_login_required
def get_emp_logged_in_count_today(request):
    o_id = request.session['o_id']
    total_emps = Employee.objects.filter(o_id_id=o_id).count()
    logged_in_count = AttendanceLogs.objects.filter(o_id=o_id, a_date=datetime.datetime.today().strftime('%Y-%#m-%#d'), a_status=1).count()
    return JsonResponse({'total_emps':total_emps, 'logged_in_count':logged_in_count})

@csrf_exempt
def logout(request):
    if request.method == 'POST':
        try:
            for key in list(request.session.keys()):
                del request.session[key]
            messages.success(request, "You are logout successfully!")
            return HttpResponseRedirect('/')
        except:
            messages.error(request, "Some error was occurred in logout!")
            return HttpResponseRedirect('/')
