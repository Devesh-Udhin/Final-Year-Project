from django.shortcuts import render, redirect
from . import data_preprocessing
import keras
import pandas as pd
import os
from ATS_HelpDesk import views as firestore
from datetime import date
from google.cloud import firestore as gc_firestore
from django.contrib.auth import logout

# Get the current user logged in
caller = None

def TicketList(request):
     
     ticketLists = firestore.DisplayTicket(request.session['user_email'])
     
     return render(request, 'base/ticket_list.html', {'ticketLists':ticketLists})

def TechDashboard(request):

     techDisctionary = {
          "tech0@gmail.com": 'Technician GRP 0',
          "tech1@gmail.com": 'Technician GRP 1',
          "tech2@gmail.com": 'Technician GRP 2',
          "tech3@gmail.com": 'Technician GRP 3',
          "tech4@gmail.com": 'Technician GRP 4',
          "tech5@gmail.com": 'Technician GRP 5',
     }

     techAssignedTickets = firestore.GetTechTickets(request.session['user_email'])
     
     return render(request, 'base/tech_dashboard.html', {'techAssignedTickets': techAssignedTickets, 'cuurentTech': techDisctionary[request.session['user_email']]})

def TechDashboardDetails(request, ticketID):
     if request.method == 'GET':
          button_action = request.GET.get('button_action')
     
          if button_action == 'back':
               return redirect('/tech_dashboard/')
          elif button_action == 'resolve':
               ticket = firestore.GetTicket(ticketID)
               firestore.UpdateResolvedTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Resolved", ticket['TechAssigned'], ticket['Date'])
               firestore.DeleteResolvedTickets(ticketID)
               return redirect('/tech_dashboard/')
     
     ticketDetails = firestore.DisplayTicketDetails(ticketID)
     techLists = firestore.GetTechList()
     ticketDetail = {'ticketDetail': ticketDetails, 'techLists': techLists}
     
     return render(request, 'base/tech_dashboard_details.html', ticketDetail)

def Login(request):
     global caller
     caller = None
     logout(request)

     if request.method == 'POST':
          
          email = request.POST.get('email')
          password = request.POST.get('password')
          
          if firestore.sign_in(email, password) == True:
               user = firestore.GetUserType(email)
               request.session['user_email'] = email
               request.session['user_type'] = user['UserType']
               
               if request.session['user_type'] == "User":
                    return redirect('create_ticket/')
               
               elif request.session['user_type'] == "Technician":
                    return redirect('tech_dashboard/')
               
               elif request.session['user_type'] == "Admin":
                    return redirect('admin/')
          
          elif firestore.sign_in(email, password) == False:
               context = {'message': 'Invalid Credentials'}
               return render(request, 'base/login.html', context)
          
          else:
               return render(request, 'base/login.html')
          
     return render(request, 'base/login.html')

# load model
model_path = os.path.join(os.path.dirname(__file__), 'model.h5')
model = keras.models.load_model(model_path)

def CreateTicket(request):
     tech =''
     description = None
     title = None
     todayDate = None
     
     if request.method == 'POST':
          description = request.POST.get('description')
          title = request.POST.get('title')
          
          if description is None or title is None:
               return render(request, 'base/create_ticket.html')
          else: 
               preProcessDescription = data_preprocessing.pre_process_data(description)
               # print("pre processed description: ", preProcessDescription)
               
               empty_list_of_lists = []
               empty_list_of_lists.append(preProcessDescription)
               
               vectorized_desc = data_preprocessing.getData(empty_list_of_lists)
               # print("vectorized description: ", vectorized_desc)

               pred = model.predict(vectorized_desc)
               # df_pred = pd.DataFrame(pred, columns=['tech1', 'tech2', 'tech3', 'tech4', 'tech5', 'tech6', 'tech7', 'tech8'])
               pred = [i.argmax() for i in pred]

               tech = pred[0]
               tech = str(tech)
               
               read()
               
               todayDate = date.today()
               # Convert the date to a Firestore timestamp
               timestamp = gc_firestore.SERVER_TIMESTAMP if isinstance(todayDate, type(date.today())) else todayDate

               status = 'Pending'
               caller = request.session.get('user_email')
     
               firestore.CreateTicket(ticketID, title, description, timestamp, status, tech, caller)
               
               write()
     
     return render(request, 'base/create_ticket.html')

def Resolve(request):
     
     ticketLists = firestore.DisplayTicketFeedback(request.session['user_email'])
     
     return render(request, 'base/resolve.html', {'ticketLists':ticketLists})

def ResolveDetails(request, ticketID):
     
     if request.method == 'GET':     
          return redirect('/resolve/')
     
     ticketDetails = firestore.DisplayAllTicketFeedback(ticketID)
     
     return render(request, 'base/resolve_details.html', {'ticketDetails':ticketDetails})

def TechResolvedTickets(request):
     
     currentTech = request.session['user_email']
     
     TechNumber = ''.join(filter(str.isdigit, currentTech))
     
     ticketDetails = firestore.DisplayTechResolvedTicket(TechNumber)
     
     return render(request, 'base/resolved_tickets.html', {'ticketDetails':ticketDetails})



ticketID = ''

def read():
     # Open the file in write mode
     file_path = os.path.join(os.path.dirname(__file__), 'TicketID.txt')
     file = open(file_path, 'r')
     # Read content from the file
     global ticketID
     ticketID = file.read()
     # Close the file
     file.close()
     
def write():
     # Open the file in write mode
     file_path = os.path.join(os.path.dirname(__file__), 'TicketID.txt')
     file = open(file_path, 'w')
     # Update the integer value
     new_value = int(ticketID) + 1
     file.write(str(new_value))
     # Close the file
     file.close()