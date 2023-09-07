$(document).ready(function() {

     let techChart = document.getElementById('techChart').getContext('2d');

     let TChart = new Chart(techChart, {
          type: 'doughnut',
          data: {
               labels: ['Pending', 'Resolved', 'Returned'],
               datasets: [{
                    label: "Number of Tickets",
                    data: [],
                    backgroundColor: ['red', 'green', 'blue'],
               }]
          },
          options: {
          }
     });

     let dateChart = document.getElementById('dateChart').getContext('2d');

     let DChart = new Chart(dateChart, {
          type: 'bar',
          data: {
               labels: ['Pending', 'Resolved', 'Returned'],
               datasets: [{
                    label: "Number of Tickets",
                    data: [],
                    backgroundColor: ['red', 'green', 'blue'],
               }]
          },
          options: {
          }
     });

     let techDateChart = document.getElementById('techDateChart').getContext('2d');

     let TDChart = new Chart(techDateChart, {
          type: 'pie',
          data: {
               labels: ['Pending', 'Resolved', 'Returned'],
               datasets: [{
                    label: "Number of Tickets",
                    data: [],
                    backgroundColor: ['red', 'green', 'blue'],
               }]
          },
          options: {
          }
     });

     $("#tech_button").click(function(event) {
          let selected_tech = $("#my_dropdown").val();
          var csrf = $("input[name=csrfmiddlewaretoken]").val();
          event.preventDefault();
    
          $.ajax({
               type: "POST",
               url: "/admin_dashboard/",
               data: {
                    csrfmiddlewaretoken: csrf,
                    technician: selected_tech,
               },
               success: function(response) {
                    var pending = response['pending'];
                    var resolved = response['resolved'];
                    var returned = response['returned'];

                    $(".tech_chart-container").removeClass("hidden");

                    TChart.data.datasets[0].data = [pending, resolved, returned];
                    TChart.update();
              
               },
               error: function(error) {
                   alert(error);
               }
          });
     });

     $("#date_button").click(function(event) {
          let start_date = $("#start_date").val();
          let end_date = $("#end_date").val();
          var csrf = $("input[name=csrfmiddlewaretoken]").val();
          event.preventDefault();
    
          $.ajax({
               type: "POST",
               url: "/admin_dashboard/",
               data: {
                    csrfmiddlewaretoken: csrf,
                    sDate: start_date,
                    eDate: end_date,
               },
               success: function(response) {

                    var pending = response['pending'];
                    var resolved = response['resolved'];
                    var returned = response['returned'];

                    $(".date_chart-container").removeClass("hidden");

                    DChart.data.datasets[0].data = [pending, resolved, returned];
                    DChart.update();
              
               },
               error: function(error) {
                   alert(error);
               }
          });
     });

     $("#tech_date_button").click(function(event) {
          let start_date = $("#tech_start_date").val();
          let end_date = $("#tech_end_date").val();
          let selected_date_tech = $("#tech_date_dropdown").val();
          var csrf = $("input[name=csrfmiddlewaretoken]").val();
          event.preventDefault();
    
          $.ajax({
               type: "POST",
               url: "/admin_dashboard/",
               data: {
                    csrfmiddlewaretoken: csrf,
                    TSDate: start_date,
                    TEDate: end_date,
                    TDSelection: selected_date_tech,
               },
               success: function(response) {

                    var pending = response['pending'];
                    var resolved = response['resolved'];
                    var returned = response['returned'];

                    $(".tech_date_chart-container").removeClass("hidden");

                    TDChart.data.datasets[0].data = [pending, resolved, returned];
                    TDChart.update();
              
               },
               error: function(error) {
                   alert(error);
               }
          });
     });


     $("#table_button").click(function(event) {
          let selection = $("#my_dropdown2").val();
          var csrf = $("input[name=csrfmiddlewaretoken]").val();
          event.preventDefault();
  
          $.ajax({
               type: "POST",
               url: "/admin_dashboard/",
               data: {
                    csrfmiddlewaretoken: csrf,
                    select_option: selection,
               },
               success: function(response) {
                    // alert(response['ticketLists'][0]['id'])
                    $('#ticket-list tbody').empty();

                    var ticketLists = response.ticketLists;
                    for (var i = 0; i < ticketLists.length; i++) {
                        var ticket = ticketLists[i];
                         
                         var newRow = '<tr>' +
                         '<td>' + ticket.id + '</td>' +
                         '<td>' + ticket.Title + '</td>' +
                         '<td>' + ticket.TechAssigned + '</td>' +
                         '<td>' + ticket.DateCreated + '</td>' +
                         '<td>' + ticket.Status + '</td>' +
                         '</tr>';


                        $('#ticket-list tbody').append(newRow);
                    }
               },
               error: function(error) {
                   alert(error);
               }
          });
     });

 });