from django.shortcuts import render, redirect
from django.http import JsonResponse
from . import data_preprocessing
import keras
import pandas as pd
import numpy as np
import os
from ATS_HelpDesk import views as firestore
from datetime import date, datetime
from google.cloud import firestore as gc_firestore
from django.contrib.auth import logout
from googletrans import Translator
from django.core.mail import EmailMessage
import base64
translator = Translator()

# =============================================Start Login=======================================================

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
                    return redirect('admin_dashboard/')
          
          elif firestore.sign_in(email, password) == False:
               context = {'message': 'Invalid Credentials'}
               return render(request, 'base/login.html', context)
          
          else:
               return render(request, 'base/login.html')
          
     return render(request, 'base/login.html')

# =============================================End Login=========================================================

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Start User's Side<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# =============================================Start User's Pending Tickets list=================================

def TicketList(request):
     
     ticketLists = firestore.DisplayTicket(request.session['user_email'])
     escalatedTicketLists = firestore.DisplayUserEscalatedTicket(request.session['user_email'])
     returnedTicketLists = firestore.DisplayUserReturnedTicket(request.session['user_email'])
     
     for ticket in escalatedTicketLists:
          ticket['Date'] = ticket.pop('DateCreated')
          ticket['TechAssigned'] = ticket.pop('TechTransferTo')
          ticket['Status'] = "Pending"
          ticketLists.append(ticket)

     for ticket in returnedTicketLists:
          ticket['Date'] = ticket.pop('DateCreated')
          ticketLists.append(ticket)
          
     for ticket in ticketLists:
          if ticket['OriginalLang'] != 'en':
               ticket['Description'] = translator.translate(ticket['Description'], dest=ticket['OriginalLang']).text
               ticket['Title'] = translator.translate(ticket['Title'], dest=ticket['OriginalLang']).text
          
     return render(request, 'base/ticket_list.html', {'ticketLists':ticketLists})

# =============================================End User's Pending Tickets list===================================

# =============================================Start User's Create Ticket======================================
# load model
model_path = os.path.join(os.path.dirname(__file__), 'model.h5')
model = keras.models.load_model(model_path)
caller = None
ticketID = ''

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

               detected_lang = translator.detect(description).lang
               if detected_lang != 'en':
                    description = translator.translate(description, dest='en').text
                    title = translator.translate(title, dest='en').text
               
               # Handle the uploaded file
               attachment = request.FILES.get('attachment')  # 'attachment' matches the 'name' attribute in your HTML form
               print(attachment)

               if attachment:
                   # Encode the file to Base64
                   encoded_attachment = base64.b64encode(attachment.read()).decode('utf-8')
               else:
                    encoded_attachment = ""
               
               preProcessDescription = data_preprocessing.pre_process_data(description)
               
               empty_list_of_lists = []
               empty_list_of_lists.append(preProcessDescription)
               
               vectorized_desc = data_preprocessing.getData(empty_list_of_lists)

               pred = model.predict(vectorized_desc)
               # df_pred = pd.DataFrame(pred, columns=['tech1@gmail.com', 'tech2@gmail.com', 'tech3@gmail.com', 'tech4@gmail.com', 'tech5@gmail.com', 'tech6@gmail.com', 'tech7@gmail.com', 'tech8@gmail.com'])
               
               # final_pred = [i.argmax() for i in pred]

               indices_descending = np.argsort(pred[0])[::-1]

               prediction_dict = {}
               
               for index in indices_descending:
                    email_string = "atsdjangotech" + str(index) + "@gmail.com"
                    prediction_dict[email_string] = pred[0][index]

               prediction_list = ["atsdjangotech" + str(index) + "@gmail.com" for index in indices_descending]
               
               print("=================================================================================================================")
               print("prediction_dict: ", prediction_dict)
               print("=================================================================================================================")
               
               read()
               
               todayDate = date.today()
               timestamp = gc_firestore.SERVER_TIMESTAMP if isinstance(todayDate, type(date.today())) else todayDate
               status = 'Pending'
               caller = request.session.get('user_email')
     
               # firestore.UpdateAttachements(ticketID, encoded_attachment)
               firestore.UpdateTicketInfoTable(ticketID, prediction_list, encoded_attachment)
               maxActiveCount = firestore.GetMaxActiveCount()
               threshold = firestore.GetThreshold()
               techActiveCount = firestore.GetAllActiveCount()
               # techActiveCountInRange = firestore.GetTechActiveCount(maxActiveCount['MaxCount'])
                                             
               # for i in prediction_list:
               #      for tech in techActiveCountInRange:
               #           if i == tech.get('id'):
               #                firestore.CreateTicket(ticketID, title, description, timestamp, status, i, caller, detected_lang)
               #                SendEmail("New Ticket Assignment", "atsdjangomain@gmail.com", ['atsdjango'+i], ticketID, str(todayDate), caller, "create")
               #                firestore.UpdateActiveCount(i, "increment")
               #                write()
               #                return render(request, 'base/create_ticket.html')
                              
               # for pred_tech, probability in prediction_dict.items():
               #      for tech in techActiveCountInRange:
               #           if pred_tech == tech.get('id') and float(probability) >= float(threshold['Threshold']):
               #                firestore.CreateTicket(ticketID, title, description, timestamp, status, pred_tech, caller, detected_lang)
               #                SendEmail("New Ticket Assignment", "atsdjangomain@gmail.com", ['atsdjango'+pred_tech], ticketID, str(todayDate), caller, "create")
               #                firestore.UpdateActiveCount(pred_tech, "increment")
               #                write()
               #                return render(request, 'base/create_ticket.html')
                         
               #           elif float(probability) >= float(threshold['Threshold']):
               #                list_of_valid_tech.append(pred_tech)

               list_of_valid_tech = []
               dict_of_valid_tech = {}
               print("Tech active count: ", techActiveCount)
               for pred_tech, probability in prediction_dict.items():
                    if float(probability) >= float(threshold['Threshold']):
                         for tech in techActiveCount:
                              if pred_tech == tech['id']:
                                   if tech['ActiveCount'] < maxActiveCount['MaxCount']:
                                        # here tech has good threshold and is free
                                        firestore.CreateTicket(ticketID, title, description, timestamp, status, pred_tech, caller, detected_lang)
                                        # SendEmail("New Ticket Assignment", "atsdjangomain@gmail.com", [pred_tech], ticketID, str(todayDate), caller, "create")
                                        firestore.UpdateActiveCount(pred_tech, "increment")
                                        write()
                                        return render(request, 'base/create_ticket.html')
                                   
                                   else:
                                        # here tech has good threshold but not free
                                        dict_of_valid_tech['id'] = pred_tech
                                        dict_of_valid_tech['count'] = tech['ActiveCount']
                                        list_of_valid_tech.append(dict_of_valid_tech)
                                        
                         min_count = min(d['count'] for d in list_of_valid_tech)
                         min_dicts = []

                         for d in list_of_valid_tech:
                             if d['count'] == min_count:
                                 min_dicts.append(d)

                         firestore.CreateTicket(ticketID, title, description, timestamp, status, min_dicts[0]['id'], caller, detected_lang)
                         # SendEmail("New Ticket Assignment", "atsdjangomain@gmail.com", [min_dicts[0]['id']], ticketID, str(todayDate), caller, "create")
                         firestore.UpdateActiveCount(min_dicts[0]['id'], "increment")
                         write()
                         return render(request, 'base/create_ticket.html')

     
     return render(request, 'base/create_ticket.html')

# =============================================End User's Create Ticket======================================

# =============================================Start User's Resolve Ticket===================================

def Resolve(request):
     
     ticketLists = firestore.DisplayTicketFeedback(request.session['user_email'])
     
     for ticket in ticketLists:
          if ticket['OriginalLang'] != 'en':
               ticket['Description'] = translator.translate(ticket['Description'], dest=ticket['OriginalLang']).text
               ticket['Title'] = translator.translate(ticket['Title'], dest=ticket['OriginalLang']).text
               ticket['Comments'] = translator.translate(ticket['Comments'], dest=ticket['OriginalLang']).text
     
     return render(request, 'base/resolve.html', {'ticketLists':ticketLists})

def ResolveDetails(request, ticketID):
     
     if request.method == 'POST':
          button_action = request.POST.get('button_action')
          
          if(button_action == 'back'):
               return redirect('/resolve/')
          
          elif(button_action == 're-send'):
               
               UserComment = request.POST.get('comment')
               
               # Detect the language of the sentence
               detected_lang = translator.detect(UserComment).lang
               if detected_lang != 'en':
                    UserComment = translator.translate(UserComment, dest='en').text

               DateResponded = date.today()
               
               ticket = firestore.GetResolvedTicket(ticketID)
               
               firestore.UpdateReturnedTable(ticketID, ticket['Caller'], ticket['Title'], ticket['Description'], ticket['TechResolved'], ticket['DateCreated'], ticket['Comments'], UserComment, ticket['OriginalLang'])
               firestore.DeleteResolvedTickets(ticketID)
               # SendEmail("New Responded Ticket", "atsdjangomain@gmail.com", [ticket['TechResolved']], ticketID, str(DateResponded), ticket['Caller'], "respond")
               return redirect('/resolve/')
               
     
     ticketDetails = firestore.GetResolvedTicket(ticketID)
     attLink = firestore.GetAttachements(ticketID)
     ticketDetails['Attachements'] = attLink

     if ticketDetails['OriginalLang'] != 'en':
          ticketDetails['Description'] = translator.translate(ticketDetails['Description'], dest=ticketDetails['OriginalLang']).text
          ticketDetails['Title'] = translator.translate(ticketDetails['Title'], dest=ticketDetails['OriginalLang']).text
          ticketDetails['Comments'] = translator.translate(ticketDetails['Comments'], dest=ticketDetails['OriginalLang']).text
     
     return render(request, 'base/resolve_details.html', {'ticketDetails':ticketDetails})

# =============================================End User's Resolve Ticket=====================================

# ========================================Start User's Attention Required Ticket=============================

def AttentionRequired(request):
     
     ticketLists = firestore.DisplayAttentionRequiredTicket(request.session['user_email'])
     for ticket in ticketLists:
          if ticket['OriginalLang'] != 'en':
               ticket['Description'] = translator.translate(ticket['Description'], dest=ticket['OriginalLang']).text
               ticket['Title'] = translator.translate(ticket['Title'], dest=ticket['OriginalLang']).text
               ticket['TechComment'] = translator.translate(ticket['TechComment'], dest=ticket['OriginalLang']).text
     
     return render(request, 'base/attention_required.html', {'ticketLists':ticketLists})

def AttentionRequiredDetails(request, ticketID):
     
     if request.method == 'POST':
          button_action = request.POST.get('button_action')
          
          if(button_action == 'back'):
               return redirect('/attention_required/')
          
          elif(button_action == 'respond'):
               UserComment = request.POST.get('responce')
               
               # Detect the language of the sentence
               detected_lang = translator.detect(UserComment).lang
               if detected_lang != 'en':
                    UserComment = translator.translate(UserComment, dest='en').text
               
               DateResponded = date.today()
               
               ticket = firestore.DisplayAllAttentionRequiredTicket(ticketID)               
               firestore.UpdateReturnedTable(ticketID, ticket['Caller'], ticket['Title'], ticket['Description'], ticket['TechAssigned'], ticket['DateCreated'], ticket['TechComment'], UserComment, ticket['OriginalLang'])
               firestore.DeleteAtentionRequiredTickets(ticketID)
               # SendEmail("New Responded Ticket", "atsdjangomain@gmail.com", [ticket['TechAssigned']], ticketID, str(DateResponded), ticket['Caller'], "respond")
               return redirect('/attention_required/')
          
     
     ticketDetails = firestore.DisplayAllAttentionRequiredTicket(ticketID)
     attLink = firestore.GetAttachements(ticketID)
     ticketDetails['Attachements'] = attLink
    
     if ticketDetails['OriginalLang'] != 'en':
          ticketDetails['Description'] = translator.translate(ticketDetails['Description'], dest=ticketDetails['OriginalLang']).text
          ticketDetails['Title'] = translator.translate(ticketDetails['Title'], dest=ticketDetails['OriginalLang']).text
          ticketDetails['TechComment'] = translator.translate(ticketDetails['TechComment'], dest=ticketDetails['OriginalLang']).text
     
     return render(request, 'base/attention_required_details.html', {'ticketDetails':ticketDetails})

# ========================================End User's Attention Required Ticket====================================

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>End User's Side<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Start Technicians's Side<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# ========================================Start Tech's Resolved Ticket===========================================
def TechResolvedTickets(request):
     
     currentTech = request.session['user_email']
     
     # isdigit id used to check if a string is a number
     # TechNumber = ''.join(filter(str.isdigit, currentTech))
     
     ticketDetails = firestore.DisplayTechResolvedTicket(currentTech)
     
     return render(request, 'base/tech_resolved_tickets.html', {'ticketDetails':ticketDetails})

def TechResolvedTicketsDetails(request, ticketID):
     
     if request.method == 'GET':
          return redirect('/tech_resolved_tickets/')
     
     ticketDetails = firestore.GetResolvedTicket(ticketID)
     attLink = firestore.GetAttachements(ticketID)
     ticketDetails['Attachements'] = attLink
     
     return render(request, 'base/tech_resolved_tickets_details.html', {'ticketDetails':ticketDetails})

# ========================================End Tech's Resolved Ticket===============================================

# ========================================Start Tech's All Resolved Ticket===========================================

def TechAllResolve(request):
     ticketDetails = firestore.GetAllResolvedTickets()
     return render(request, 'base/all_resolve.html', {'ticketDetails':ticketDetails})

# ========================================End Tech's All Resolved Ticket===============================================

# =============================================Start Tech Dashboard================================================

def TechDashboard(request):

     techAssignedTickets = firestore.GetTechTickets(request.session['user_email'])
     
     return render(request, 'base/tech_dashboard.html', {'techAssignedTickets': techAssignedTickets, 'cuurentTech': techDisctionary[request.session['user_email']]})

def TechDashboardDetails(request, ticketID):
     if request.method == 'POST':
          button_action = request.POST.get('button_action')
          DateResponded = date.today()
          if button_action == 'back':
               return redirect('/tech_dashboard/')
          
          elif button_action == 'resolve':
               how_ticket_was_resolve = request.POST.get('how_ticket_was_resolve')
               comment = request.POST.get('comment')
               ticket = firestore.DisplayTicketDetails(ticketID)

               firestore.UpdateResolvedTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Resolved", ticket['TechAssigned'], ticket['Date'], comment, how_ticket_was_resolve, ticket['OriginalLang'])
               
               firestore.DeleteTickets(ticketID)
               # update active count
               firestore.UpdateActiveCount(ticket['TechAssigned'], "decrement")
               # update resolve count
               firestore.UpdateResolveCount(ticket['TechAssigned'], "increment")
               
               # SendEmail("New Resolved Ticket", "atsdjangomain@gmail.com", [ticket['Caller']], ticketID, str(DateResponded), ticket['Caller'], "resolve")
               
               return redirect('/tech_dashboard/')
          
          elif button_action == 'transfer':
               TechComment = request.POST.get('TechComment')
               TechEscalatedTo = request.POST.get('selected_technician')
               ticket = firestore.DisplayTicketDetails(ticketID)
               firestore.UpdateEscalatedTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Escalated", ticket['TechAssigned'], techDisctionary2[TechEscalatedTo], ticket['Date'], TechComment, ticket['OriginalLang'])
               firestore.DeleteTickets(ticketID)
               
               # update active count
               firestore.UpdateActiveCount(ticket['TechAssigned'], "decrement")
               firestore.UpdateActiveCount(techDisctionary2[TechEscalatedTo], "increment")
               
               # SendEmail("New Transfered Ticket", "atsdjangomain@gmail.com", [techDisctionary2[TechEscalatedTo]], ticketID, str(DateResponded), ticket['Caller'], "escalate")
               
               return redirect('/tech_dashboard/')
               
          elif button_action == 'auto_transfer':
               TechComment = request.POST.get('TechComment')
               predictions = firestore.GetPredictionsList(ticketID)
               maxActiveCount = firestore.GetMaxActiveCount()
               techActiveCountInRange = firestore.GetTechActiveCount(maxActiveCount['MaxCount'])
               key_to_compare = "id"
               ticket = firestore.DisplayTicketDetails(ticketID)
               
               for i in predictions:
                    for tech in techActiveCountInRange:
                         if i == tech.get(key_to_compare) and i != ticket['TechAssigned']:
                              TechEscalatedTo = i
                              firestore.UpdateAutoEscalatedTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Escalated", ticket['TechAssigned'], TechEscalatedTo, ticket['Date'], TechComment, ticket['OriginalLang'])
                              firestore.DeleteTickets(ticketID)
                              firestore.UpdateActiveCount(ticket['TechAssigned'], "decrement")
                              firestore.UpdateActiveCount(TechEscalatedTo, "increment")
                              # SendEmail("New Transfered Ticket", "atsdjangomain@gmail.com", [TechEscalatedTo], ticketID, str(DateResponded), ticket['Caller'], "escalate")
                              return redirect('/tech_dashboard/')

               return redirect('/tech_dashboard/')
          
          elif button_action == 'request':
               request_message = request.POST.get('request_message')
               ticket = firestore.DisplayTicketDetails(ticketID)               
               firestore.UpdateAttentionRequiredTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Attention_Required", ticket['TechAssigned'], ticket['Date'], request_message, ticket['OriginalLang'])
               firestore.DeleteTickets(ticketID)
               
               # update active count
               firestore.UpdateActiveCount(ticket['TechAssigned'], "decrement")
               # SendEmail("New Attention Needed Ticket", "atsdjangomain@gmail.com", [ticket['Caller']], ticketID, str(DateResponded), ticket['Caller'], "info")
               return redirect('/tech_dashboard/')
     
     ticketDetails = firestore.DisplayTicketDetails(ticketID)
     attLink = firestore.GetAttachements(ticketID)
     ticketDetails['Attachements'] = attLink
     
     techLists = firestore.GetTechList()
     ticketDetail = {'ticketDetail': ticketDetails, 'techLists': techLists}
     
     return render(request, 'base/tech_dashboard_details.html', ticketDetail)

# =============================================End Tech Dashboard================================================

# ========================================Start Tech Escalated Tickets=============================================
def TechEscalatedTicket(request):
     
     ticketLists = firestore.DisplayTechEscalatedTicket(request.session['user_email'])
     
     return render(request, 'base/escalated.html', {'ticketLists':ticketLists, 'cuurentTech': techDisctionary[request.session['user_email']]})

def TechEscalatedTicketDetails(request, ticketID):
          
     if request.method == 'POST':
          button_action = request.POST.get('button_action')
          DateResponded = date.today()
          if button_action == 'back':
               return redirect('/escalated/')

          elif button_action == 'resolve':
               how_ticket_was_resolve = request.POST.get('how_ticket_was_resolve')
               comment = request.POST.get('comment')
               ticket = firestore.GetEscalatedTicket(ticketID)
               firestore.UpdateResolvedTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Resolved", ticket['TechTransferTo'], ticket['DateCreated'], comment, how_ticket_was_resolve, ticket['OriginalLang'])

               firestore.DeleteEscalatedTickets(ticketID) 
               # update active count
               firestore.UpdateActiveCount(ticket['TechTransferTo'], "decrement")
               # update resolve count
               firestore.UpdateResolveCount(ticket['TechTransferTo'], "increment")
               # SendEmail("New Resolved Ticket", "atsdjangomain@gmail.com", [ticket['Caller']], ticketID, str(DateResponded), ticket['Caller'], "resolve")
               return redirect('/escalated/')

          elif button_action == 'transfer':
               TechComment = request.POST.get('TechComment')
               TechEscalatedTo = request.POST.get('selected_technician')
               ticket = firestore.GetEscalatedTicket(ticketID)
               firestore.UpdateEscalatedTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Escalated", ticket['TechTransferTo'], techDisctionary2[TechEscalatedTo], ticket['DateCreated'], TechComment, ticket['OriginalLang'])

               # update active count
               firestore.UpdateActiveCount(ticket['TechTransferTo'], "decrement")
               firestore.UpdateActiveCount(techDisctionary2[TechEscalatedTo], "increment")
               # SendEmail("New Transfered Ticket", "atsdjangomain@gmail.com", [techDisctionary2[TechEscalatedTo]], ticketID, str(DateResponded), ticket['Caller'], "escalate")
               return redirect('/escalated/')

          elif button_action == 'auto_transfer':
               TechComment = request.POST.get('TechComment')
               predictions = firestore.GetPredictionsList(ticketID)
               maxActiveCount = firestore.GetMaxActiveCount()
               techActiveCountInRange = firestore.GetTechActiveCount(maxActiveCount['MaxCount'])
               
               key_to_compare = "id"
               ticket = firestore.GetEscalatedTicket(ticketID)
               
               for i in predictions:
                    for tech in techActiveCountInRange:
                         if i == tech.get(key_to_compare) and i != ticket['TechTransferTo']:
                              TechEscalatedTo = i
                              firestore.UpdateAutoEscalatedTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Escalated", ticket['TechTransferTo'], TechEscalatedTo, ticket['DateCreated'], TechComment, ticket['OriginalLang'])
                              firestore.UpdateActiveCount(ticket['TechTransferTo'], "decrement")
                              firestore.UpdateActiveCount(TechEscalatedTo, "increment")
                              # SendEmail("New Transfered Ticket", "atsdjangomain@gmail.com", [TechEscalatedTo], ticketID, str(DateResponded), ticket['Caller'], "escalate")
                              return redirect('/escalated/')

               return redirect('/escalated/')

          elif button_action == 'request':
               request_message = request.POST.get('request_message')
               ticket = firestore.GetEscalatedTicket(ticketID)
               firestore.UpdateAttentionRequiredTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Attention_Required", ticket['TechTransferTo'], ticket['DateCreated'], request_message, ticket['OriginalLang'])
               firestore.DeleteEscalatedTickets(ticketID)

               # update active count
               firestore.UpdateActiveCount(ticket['TechTransferTo'], "decrement")
               # SendEmail("New Attention Needed Ticket", "atsdjangomain@gmail.com", [ticket['Caller']], ticketID, str(DateResponded), ticket['Caller'], "info")
               return redirect('/escalated/')

     
     ticketDetails = firestore.GetEscalatedTicket(ticketID)
     attLink = firestore.GetAttachements(ticketID)
     ticketDetails['Attachements'] = attLink

     techLists = firestore.GetTechList()
     ticketDetail = {'ticketDetail': ticketDetails, 'techLists': techLists}
     return render(request, 'base/escalated_details.html', ticketDetail)

# ========================================End Tech Escalated Tickets=============================================

# ========================================Start Tech's Returned Ticket===========================================
def TechReturnedTicket(request):
     
     ticketLists = firestore.DisplayReturnedTicket(request.session['user_email'])
     
     return render(request, 'base/return.html', {'ticketLists':ticketLists, 'cuurentTech': techDisctionary[request.session['user_email']]})

def TechReturnedTicketDetails(request, ticketID):
          
     if request.method == 'POST':
          button_action = request.POST.get('button_action')
          DateResponded = date.today()
          if button_action == 'back':
               return redirect('/return/')

          elif button_action == 'resolve':
               how_ticket_was_resolve = request.POST.get('how_ticket_was_resolve')
               comment = request.POST.get('comment')
               ticket = firestore.DisplayAllReturnedTicket(ticketID)
               firestore.UpdateResolvedTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Resolved", ticket['TechAssigned'], ticket['DateCreated'], comment, how_ticket_was_resolve, ticket['OriginalLang'])

               firestore.DeleteReturnedTickets(ticketID) 
               # update active count
               firestore.UpdateActiveCount(ticket['TechAssigned'], "decrement")
               # update resolve count
               firestore.UpdateResolveCount(ticket['TechAssigned'], "increment")
               # SendEmail("New Resolved Ticket", "atsdjangomain@gmail.com", [ticket['Caller']], ticketID, str(DateResponded), ticket['Caller'], "resolve")
               return redirect('/return/')

          elif button_action == 'transfer':
               TechComment = request.POST.get('TechComment')
               TechEscalatedTo = request.POST.get('selected_technician')
               ticket = firestore.DisplayAllReturnedTicket(ticketID)
               firestore.UpdateEscalatedTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Escalated", ticket['TechAssigned'], techDisctionary2[TechEscalatedTo], ticket['DateCreated'], TechComment, ticket['OriginalLang'])
               firestore.DeleteReturnedTickets(ticketID)

               # update active count
               firestore.UpdateActiveCount(ticket['TechAssigned'], "decrement")
               firestore.UpdateActiveCount(techDisctionary2[TechEscalatedTo], "increment")
               # SendEmail("New Transfered Ticket", "atsdjangomain@gmail.com", [techDisctionary2[TechEscalatedTo]], ticketID, str(DateResponded), ticket['Caller'], "escalate")
               return redirect('/return/')

          elif button_action == 'auto_transfer':
               TechComment = request.POST.get('TechComment')
               predictions = firestore.GetPredictionsList(ticketID)
               maxActiveCount = firestore.GetMaxActiveCount()
               techActiveCountInRange = firestore.GetTechActiveCount(maxActiveCount['MaxCount'])
               
               key_to_compare = "id"
               ticket = firestore.DisplayAllReturnedTicket(ticketID)
               
               for i in predictions:
                    for tech in techActiveCountInRange:
                         if i == tech.get(key_to_compare) and i != ticket['TechAssigned']:
                              TechEscalatedTo = i
                              firestore.UpdateAutoEscalatedTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Escalated", ticket['TechAssigned'], TechEscalatedTo, ticket['DateCreated'], TechComment, ticket['OriginalLang'])
                              firestore.DeleteReturnedTickets(ticketID)
                              firestore.UpdateActiveCount(ticket['TechAssigned'], "decrement")
                              firestore.UpdateActiveCount(TechEscalatedTo, "increment")
                              # SendEmail("New Transfered Ticket", "atsdjangomain@gmail.com", [TechEscalatedTo], ticketID, str(DateResponded), ticket['Caller'], "escalate")
                              return redirect('/return/')

               return redirect('/return/')

          elif button_action == 'request':
               request_message = request.POST.get('request_message')
               ticket = firestore.DisplayAllReturnedTicket(ticketID)
               firestore.UpdateAttentionRequiredTable(ticket['id'], ticket['Caller'], ticket['Title'], ticket['Description'], "Attention_Required", ticket['TechAssigned'], ticket['DateCreated'], request_message, ticket['OriginalLang'])
               firestore.DeleteReturnedTickets(ticketID)

               # update active count
               firestore.UpdateActiveCount(ticket['TechAssigned'], "decrement")
               # SendEmail("New Attention Needed Ticket", "atsdjangomain@gmail.com", [ticket['Caller']], ticketID, str(DateResponded), ticket['Caller'], "info")
               return redirect('/return/')

     
     ticketDetails = firestore.DisplayAllReturnedTicket(ticketID)
     attLink = firestore.GetAttachements(ticketID)
     ticketDetails['Attachements'] = attLink

     techLists = firestore.GetTechList()
     ticketDetail = {'ticketDetail': ticketDetails, 'techLists': techLists}
     
     return render(request, 'base/return_details.html', ticketDetail)

# ========================================End Tech's Returned Ticket=======================================

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>End Technicians's Side<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Start Admin's Side<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# =============================================Start Admin Dashboard================================================

# def AdminDashboard(request):
#      showChart = 0
#      techLists = firestore.GetTechList()
     
#      if request.method == 'POST':
#           button_action = request.POST.get('button_action')
#           if button_action == 'submit':
#                tech_selected = request.POST.get('selected_technician')
#                pending = len(firestore.GetTechTickets(techDisctionary2[tech_selected]))
#                resolved = len(firestore.DisplayTechResolvedTicket(techDisctionary2[tech_selected]))
#                returned = len(firestore.DisplayReturnedTicket(techDisctionary2[tech_selected]))
#                showChart = 1
#                technician = str(tech_selected)
#                figures = {'pending': pending, 'resolved': resolved, 'returned': returned, 'showChart': showChart, 'techLists': techLists, 'technician': technician}
               
#                return render(request, 'base/admin_dashboard.html', figures)
               
#      ticketDetail = {'techLists': techLists, 'showChart': showChart}
     
#      return render(request, 'base/admin_dashboard.html', ticketDetail)

def AdminDashboard(request):
    
    if request.method == 'POST':
         if (request.POST.get('technician') != None):
               tech_selected = request.POST.get('technician')
               pending = len(firestore.GetTechTickets(techDisctionary2[tech_selected])) + len(firestore.DisplayTechEscalatedTicket(techDisctionary2[tech_selected]))
               resolved = len(firestore.DisplayTechResolvedTicket(techDisctionary2[tech_selected]))
               returned = len(firestore.DisplayReturnedTicket(techDisctionary2[tech_selected]))

               figures = {'pending': pending, 'resolved': resolved, 'returned': returned}

               # Return a JSON response with the data
               return JsonResponse(figures)
         elif (request.POST.get('select_option') != None):
               select_option = request.POST.get('select_option')
               if (select_option == 'Pending'):
                    ticketLists = firestore.GetAllPendingTickets()
                    
                    for ticket in ticketLists:
                         ticket['DateCreated'] = ticket.pop('Date')
                    
                    return JsonResponse({"ticketLists": ticketLists})
               elif (select_option == 'Resolved'):
                    ticketLists = firestore.GetAllResolvedTickets()
                    
                    for ticket in ticketLists:
                         ticket['TechAssigned'] = ticket.pop('TechResolved')
                    
                    return JsonResponse({"ticketLists": ticketLists})
               elif (select_option == 'Escalated'):
                    ticketLists = firestore.GetAllEscalatedTickets()
                    
                    for ticket in ticketLists:
                         ticket['TechAssigned'] = ticket.pop('TechTransferTo')
                    
                    return JsonResponse({"ticketLists": ticketLists})
               elif (select_option == 'Returned'):
                    ticketLists = firestore.GetAllReturnedTickets()
                    return JsonResponse({"ticketLists": ticketLists})
               elif (select_option == 'Attention_Required'):
                    ticketLists = firestore.GetAllAttentionRequiredTickets()
                    return JsonResponse({"ticketLists": ticketLists})
               
         elif (request.POST.get('sDate') != None):
               start_date = request.POST.get('sDate')
               end_date = request.POST.get('eDate')

               start_timestamp = datetime.strptime(start_date, "%Y-%m-%d")
               end_timestamp = datetime.strptime(end_date, "%Y-%m-%d")
               
               pending = len(firestore.GetDatePendingTickets(start_timestamp, end_timestamp)) + len(firestore.GetDateEscalatedTickets(start_timestamp, end_timestamp))
               resolved = len(firestore.GetDateResolvedTickets(start_timestamp, end_timestamp))
               returned = len(firestore.GetDateReturnedTickets(start_timestamp, end_timestamp))

               figures = {'pending': pending, 'resolved': resolved, 'returned': returned}

               return JsonResponse(figures)

         elif (request.POST.get('TDSelection') != None):
               start_date = request.POST.get('TSDate')
               end_date = request.POST.get('TEDate')
               tech_selected = request.POST.get('TDSelection')

               start_timestamp = datetime.strptime(start_date, "%Y-%m-%d")
               end_timestamp = datetime.strptime(end_date, "%Y-%m-%d")
               
               list_pending = []
               list_resolved = []
               list_returned = []
               list_escalated = []
               
               pending = firestore.GetDatePendingTickets(start_timestamp, end_timestamp)

               for pt in pending:
                    if pt['TechAssigned'] == techDisctionary2[tech_selected]:
                         list_pending.append(pt)

               resolved = firestore.GetDateResolvedTickets(start_timestamp, end_timestamp)
               
               for rt in resolved:
                    if rt['TechResolved'] == techDisctionary2[tech_selected]:
                         list_resolved.append(rt)
               
               returned = firestore.GetDateReturnedTickets(start_timestamp, end_timestamp)

               for ret in returned:
                    if ret['TechAssigned'] == techDisctionary2[tech_selected]:
                         list_returned.append(ret)

               escalated = firestore.GetDateEscalatedTickets(start_timestamp, end_timestamp)
               
               for et in escalated:
                    if et['TechTransferTo'] == techDisctionary2[tech_selected]:
                         list_escalated.append(et)

               figures = {'pending': len(list_pending)+len(list_escalated), 'resolved': len(list_resolved), 'returned': len(list_returned)}

               return JsonResponse(figures)
          
    # Handle the GET request or other HTTP methods
    techLists = firestore.GetTechList()
    ticketDetail = {'techLists': techLists}
    
    return render(request, 'base/admin_dashboard.html', ticketDetail)

# =============================================End Admin Dashboard================================================

# =============================================Start Admin Rule================================================

def AdminRule(request):
     
     if request.method == 'POST':
          button_action = request.POST.get('button_action')
          
          if button_action == 'count':
               maxActiveCount = request.POST.get('maxCount')
               firestore.UpdateMaxActiveCount(maxActiveCount)
               return redirect('/admin_rule/')
          
          elif button_action == 'threshold':
               threshold = request.POST.get('setThreshold')
               firestore.UpdateTechThreshold(threshold)
               return redirect('/admin_rule/')
     
     return render(request, 'base/admin_rule.html')

# =============================================End Admin Rule================================================

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>End Admin's Side<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

# 1. Create active ticket count for each technician ==============DONE============
# 2. Increament and decrement active ticket count accordingly ========DONE============
# 3. Update db for additional fields like comment etc ==============DONE============
# 4. Create table for all resolved tickets and how it was resolved ==============DONE============
# 5. Create table for all pending tickets ==============DONE============
# 6. User can re-submit tickets if problem was not solved ==============DONE============
# 7. Escalate tickets *** ==============DONE============
# 8 Translation ================DONE============
# 9. Notify technician when ticket is assigned to them ==============DONE============
# 10. Create reporting tool for admin ==============DONE============

# when a ticket is resubmitted, should add it on the pending ticket list for user ==========Done============
# change title language

# Pending tickets -> Resolved, Request, transfer, auto-transfer
# Returned tickets -> Resolved, Request, transfer, auto-transfer
# Escalated tickets -> Resolved, request, transfer, auto-transfer

# user: create ticket -> see pending -> respond attention required

# tech: dashboard: resolve -> request info -> transfer -> auto transfer
#       escalate: resolved -> request info -> transfer -> auto transfer
#       returned: resolve -> request info -> transfer -> auto transfer

def SendEmail(subject, from_email, recipient_list, ticketID, date, caller, type):

     recipient_email_address = recipient_list[0].replace("atsdjango", "").replace("@gmail.com", "")

     if type == 'create':
          full_email = '''Dear ''' + recipient_email_address + ''',

This is to inform you that a new ticket has been assigned to you. Please find the details below:

Ticket ID: ''' + ticketID + '''
Date Assigned: ''' + date + '''

Your prompt attention to this ticket is greatly appreciated. Kindly review the details and take the necessary actions to assist the requester.

Thank you for your assistance.

Best regards,
ATS Admin'''
                          
     elif type == 'escalate':                     
          full_email = '''Dear ''' + recipient_email_address + ''',

This is to inform you that a new ticket has been transfered to you. Please find the details below:

Ticket ID: ''' + ticketID + '''
Date Assigned: ''' + date + '''

Your prompt attention to this ticket is greatly appreciated. Kindly review the details and take the necessary actions to assist the requester.

Thank you for your assistance.

Best regards,
ATS Admin'''

     elif type == 'respond':
          full_email = '''Dear ''' + recipient_email_address + ''',

This is to inform you that a ticket has been responded by user ''' + caller + '''. Please find the details below:

Ticket ID: ''' + ticketID + '''
Date Responded: ''' + date + '''

Your prompt attention to this ticket is greatly appreciated. Kindly review the details and take the necessary actions to assist the requester.

Thank you for your assistance.

Best regards,
ATS Admin'''
                          
     elif type == 'resolve':
          full_email = '''Dear ''' + recipient_email_address + ''',

This is to inform you that your ticket with ID: ''' + ticketID + ''' has been resolved.

Kindly review the details and take the necessary actions provided by the technician.

Thank you for your comprehension.

Best regards,
ATS Admin'''

     elif type == 'info':
          full_email = '''Dear ''' + recipient_email_address + ''',

This is to inform you that your ticket with ID: ''' + ticketID + ''' is on hold.

Kindly review the details and provide the necessary information asked by the technician.

Thank you for your comprehension.

Best regards,
ATS Admin'''
     
     # Create an EmailMessage instance
     email = EmailMessage(subject, full_email, from_email, recipient_list)

     # # Attach files or additional content (optional)
     # email.attach_file('/path/to/attachment.pdf')

     # Send the email
     email.send()
     

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
     

techDisctionary = {
     "atsdjangotech0@gmail.com": 'Technician GRP 0',
     "atsdjangotech1@gmail.com": 'Technician GRP 1',
     "atsdjangotech2@gmail.com": 'Technician GRP 2',
     "atsdjangotech3@gmail.com": 'Technician GRP 3',
     "atsdjangotech4@gmail.com": 'Technician GRP 4',
     "atsdjangotech5@gmail.com": 'Technician GRP 5',
     "atsdjangotech6@gmail.com": 'Technician GRP 6',
     "atsdjangotech7@gmail.com": 'Technician GRP 7',
}

techDisctionary2 = {
     "GRP_0": "atsdjangotech0@gmail.com",
     "GRP_1": "atsdjangotech1@gmail.com",
     "GRP_2": "atsdjangotech2@gmail.com",
     "GRP_3": "atsdjangotech3@gmail.com",
     "GRP_4": "atsdjangotech4@gmail.com",
     "GRP_5": "atsdjangotech5@gmail.com",
     "GRP_6": "atsdjangotech6@gmail.com",
     "GRP_7": "atsdjangotech7@gmail.com",
}
