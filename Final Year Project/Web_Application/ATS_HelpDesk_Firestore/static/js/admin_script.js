let myChart = document.getElementById('myChart').getContext('2d');

let XChart = new Chart(myChart, {
     type: 'bar',
     data: {
          labels: ['a', 'b', 'c', 'd', 'e'],
          datasets: [{
               label: 'Testing',
               data: [
                    3123,
                    4324,
                    5345,
                    1231,
                    8678,
               ]
          }]
     },
     options: {}
});