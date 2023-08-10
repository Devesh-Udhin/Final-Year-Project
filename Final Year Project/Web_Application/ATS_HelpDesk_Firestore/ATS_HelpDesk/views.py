import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import date
from google.cloud import firestore as gc_firestore

# Firebase admin config
key_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)
db = firestore.client()
# End of Firebase admin config


# Authentication by pyrebase
import pyrebase

config = {
     "apiKey": "AIzaSyCJM6fqkODVsErEDkA1MxCR2zDld9jVMqg",
     "authDomain": "ats-helpdesk.firebaseapp.com",
     "databaseURL": "https://ats-helpdesk-default-rtdb.asia-southeast1.firebasedatabase.app",
     "projectId": "ats-helpdesk",
     "storageBucket": "ats-helpdesk.appspot.com",
     "messagingSenderId": "782388218722",
     "appId": "1:782388218722:web:aead06c84fae82f445ba3b",
     "measurementId": "G-YRKXS4GX4P"
}

pyrebase_firebase = pyrebase.initialize_app(config)
pyrebase_auth = pyrebase_firebase.auth()
pyrebase_database = pyrebase_firebase.database()
# End of Authentication by pyrebase

techDisctionary = {
     "tech0@gmail.com": '0',
     "tech1@gmail.com": '1',
     "tech2@gmail.com": '2',
     "tech3@gmail.com": '3',
     "tech4@gmail.com": '4',
     "tech5@gmail.com": '5',
     "tech5@gmail.com": '6',
     "tech5@gmail.com": '7',
}

def sign_in(email, password):
     try:
          pyrebase_auth.sign_in_with_email_and_password(email, password)
          return True
     except:
          # Invalid credentials or user not found
          return False


def CreateTicket(ticketID, title, description, date, status, techAssigned, caller):
     
     data = {'Title':title, 'Description':description, 'Caller':caller, 'Date':date, 'TechAssigned':techAssigned, 'Status':status}
     db.collection('Tickets').document(ticketID).set(data)
     
def DisplayTicket(caller):
     results = []
     docs = db.collection('Tickets').where('Caller', '==', caller).get()
     for doc in docs:
          data = doc.to_dict()
          data['id'] = doc.id
          results.append(data)
     return results

def GetUserType(email):
     userType = db.collection('Users').document(email).get()
     userType = userType.to_dict()
     return userType

def GetTechTickets(techEmail):
     
     tech = techDisctionary[techEmail]
     results = []
     
     assignedTickets = db.collection('Tickets').where('TechAssigned', '==', tech).get()
     
     for assignedTicket in assignedTickets:
          data = assignedTicket.to_dict()
          data['id'] = assignedTicket.id
          results.append(data)
     
     return results

def GetTechList():
     techLists = db.collection('Info').document('Technicians').get()
     print(type(techLists))
     techListsDict = techLists.to_dict()
     print(type(techListsDict))

     tech_array_data = techListsDict.get('ListOfTechnicians', [])

     return tech_array_data

def DisplayTicketDetails(ticketID):
     result = db.collection('Tickets').document(ticketID).get()
     ticket = result.to_dict()
     ticket['id'] = result.id
     
     return ticket

def DisplayTicketFeedback(caller):
     results = []
     docs = db.collection('ResolvedTickets').where('Caller', '==', caller).get()
     for doc in docs:
          data = doc.to_dict()
          data['id'] = doc.id
          results.append(data)
     return results

def DisplayAllTicketFeedback(ticketID):
     result = db.collection('ResolvedTickets').document(ticketID).get()
     ticket = result.to_dict()
     ticket['id'] = result.id
     return ticket

def UpdateResolvedTable(ticketID, Caller, Title, Description, Status, TechResolved, DateCreated):
     DateResolved = date.today()
     # Convert the date to a Firestore timestamp
     DateResolved = gc_firestore.SERVER_TIMESTAMP if isinstance(DateResolved, type(date.today())) else DateResolved

     data = {'Caller':Caller, 'Title':Title, 'Description':Description, 'Status':Status, 'TechResolved':TechResolved, 'DateCreated':DateCreated, 'DateResolved':DateResolved}
     db.collection('ResolvedTickets').document(ticketID).set(data)

def DeleteResolvedTickets(ticketID):
     db.collection('Tickets').document(ticketID).delete()
     return

def DisplayTechResolvedTicket(TechNumber):
     results = []
     docs = db.collection('ResolvedTickets').where('TechResolved', '==', TechNumber).get()
     for doc in docs:
          data = doc.to_dict()
          data['id'] = doc.id
          results.append(data)
     return results

def GetTicket(ticketID):

     ticket = db.collection('Tickets').document(ticketID).get()
     result = ticket.to_dict()
     result['id'] = ticket.id

     return result