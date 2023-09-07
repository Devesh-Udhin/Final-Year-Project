from django.urls import path
from . import views

urlpatterns = [
    # Login
    path('', views.Login, name="LoginPage"),
    # Users
    path('ticket_list/', views.TicketList, name="TicketList"),
    path('create_ticket/', views.CreateTicket, name="CreateTicket"),
    path('resolve/', views.Resolve, name="Resolve"),
    path('resolve/details/<str:ticketID>', views.ResolveDetails, name="ResolveDetails"),
    path('attention_required/', views.AttentionRequired, name="AttentionRequired"),
    path('attention_required/details/<str:ticketID>', views.AttentionRequiredDetails, name="AttentionRequiredDetails"),
    # Technicians
    path('tech_dashboard/', views.TechDashboard, name="TechDashboard"),
    path('tech_dashboard/details/<str:ticketID>', views.TechDashboardDetails, name="TechDashboardDetails"),
    path('tech_resolved_tickets/', views.TechResolvedTickets, name="TechResolvedTickets"),
    path('tech_resolved_tickets/details/<str:ticketID>', views.TechResolvedTicketsDetails, name="ResolveDetails"),
    path('return/', views.TechReturnedTicket, name="TechReturnedTicket"),
    path('return/details/<str:ticketID>', views.TechReturnedTicketDetails, name="TechReturnedTicketDetails"),
    path('escalated/', views.TechEscalatedTicket, name="TechEscalatedTicket"),
    path('escalated/details/<str:ticketID>', views.TechEscalatedTicketDetails, name="TechEscalatedTicketDetails"),
    path('all_resolve/', views.TechAllResolve, name="TechAllResolve"),
    # Admin
    path('admin_dashboard/', views.AdminDashboard, name="AdminDashboard"),
    path('admin_rule/', views.AdminRule, name="AdminDashboard"),
]