$(document).ready(function() {
    // Populate time options on page load
    populateTimeOptions();

    // Event listener for date change
    $('#your-date').on('change', function() {
        console.log('your-date Date changed');
        const date = this.value;
        console.log('date:', date);
        fetch(`/get-available-times/?date=${date}`)
            .then(response => response.json())
            .then(data => {
                console.log('Success:', data);
                const timeSelect = document.getElementById('your-time');
                timeSelect.innerHTML = '<option value="" disabled selected>Select Time</option>';
                data.available_times.forEach(time => {
                    const option = document.createElement('option');
                    option.value = time;
                    option.textContent = time;
                    timeSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error fetching available times:', error);
            });
    });

    // Function to populate time options
    function populateTimeOptions() {
        var timeSelect = document.getElementById('your-time');
        var startTime = 9;
        var endTime = 17 + (30 / 60);
        var interval = 30;

        timeSelect.innerHTML = '<option value="" disabled selected>Select Time</option>';

        for (var hour = startTime; hour <= endTime; hour += interval / 60) {
            var hourPart = Math.floor(hour);
            var minutePart = (hour * 60) % 60;

            var hourString = hourPart.toString().padStart(2, '0');
            var minuteString = minutePart.toString().padStart(2, '0');
            var timeValue = hourString + ':' + minuteString;

            var option = new Option(timeValue, timeValue);
            timeSelect.appendChild(option);
        }
    }
});
