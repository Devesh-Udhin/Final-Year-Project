from django.urls import path
from . import views

urlpatterns = [
    path('tech_dashboard/', views.TechDashboard, name="TechDashboard"),
    path('tech_dashboard/details/<str:ticketID>', views.TechDashboardDetails, name="TechDashboardDetails"),
    path('', views.Login, name="LoginPage"),
    path('ticket_list/', views.TicketList, name="TicketList"),
    path('create_ticket/', views.CreateTicket, name="CreateTicket"),
    path('resolve/', views.Resolve, name="Resolve"),
    path('resolve/details/<str:ticketID>', views.ResolveDetails, name="ResolveDetails"),
    path('resolved_tickets/', views.TechResolvedTickets, name="TechResolvedTickets"),
]