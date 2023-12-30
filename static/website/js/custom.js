$(document).ready(function() {
    // Populate time options on page load
    populateTimeOptions();

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
