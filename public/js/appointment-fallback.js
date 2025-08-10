// 备用版本 - 用于本地测试或Netlify Functions未配置时
// 生产环境应使用appointment.js

// 所有可用时间槽
const allTimeSlots = [
    '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
    '11:00', '11:30', '13:00', '13:30', '14:00', '14:30',
    '15:00', '15:30', '16:00', '16:30'
];

// 特定日期的排除时间槽
const excludedSlots = {
    '2024-12-31': ['11:00', '11:30', '15:00', '15:30'],
    '2025-01-02': ['09:30', '10:00', '10:30', '11:00', '13:00', '13:30', '14:00', '14:30'],
    '2025-01-03': ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '13:00', '13:30', '14:00'],
    '2025-01-07': ['09:30', '10:00', '10:30', '11:00', '13:00', '13:30', '14:00', '14:30'],
    '2025-01-08': ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30', '15:00', '15:30'],
    '2025-01-09': ['09:30', '10:00', '10:30', '11:00', '13:00', '13:30', '14:00', '14:30'],
    '2025-01-10': ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '13:00', '13:30', '14:00', '14:30']
};

// Initialize date picker
$(document).ready(function() {
    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    $('#appointment-date').attr('min', today);
    
    // Handle date selection
    $('#appointment-date').on('change', function() {
        const selectedDate = $(this).val();
        if (selectedDate) {
            loadAvailableTimeSlotsLocal(selectedDate);
        }
    });
    
    // Handle form submission
    $('#appointmentForm').on('submit', async function(e) {
        e.preventDefault();
        await submitAppointmentLocal();
    });
});

// Load available time slots locally (without API)
function loadAvailableTimeSlotsLocal(date) {
    const timeSelect = $('#appointment-time');
    timeSelect.empty();
    
    // Get excluded slots for this date
    const dateExclusions = excludedSlots[date] || [];
    
    // Check if selected date is today
    const selectedDateTime = new Date(date);
    const now = new Date();
    const isToday = selectedDateTime.toDateString() === now.toDateString();
    const currentTime = now.getHours() * 60 + now.getMinutes();
    
    // Filter available slots
    const availableSlots = allTimeSlots.filter(slot => {
        // Skip if slot is excluded for this date
        if (dateExclusions.includes(slot)) {
            return false;
        }
        
        // Skip past time slots for today
        if (isToday) {
            const [hours, minutes] = slot.split(':').map(Number);
            const slotTime = hours * 60 + minutes;
            if (slotTime <= currentTime) {
                return false;
            }
        }
        
        return true;
    });
    
    // Populate time selector
    if (availableSlots.length > 0) {
        timeSelect.append('<option value="">Select Time</option>');
        availableSlots.forEach(slot => {
            timeSelect.append(`<option value="${slot}">${slot}</option>`);
        });
    } else {
        timeSelect.append('<option value="">No available slots</option>');
    }
}

// Submit appointment locally (for testing)
async function submitAppointmentLocal() {
    const formMessage = $('#form-message');
    formMessage.removeClass('alert-success alert-danger').empty();
    
    // Get form data
    const formData = {
        name: $('#name').val(),
        phone: $('#phone').val(),
        email: $('#email').val(),
        service: $('#service').val() || 'Not specified',
        date: $('#appointment-date').val(),
        time: $('#appointment-time').val(),
        message: $('#message').val() || null
    };
    
    // Simulate successful submission
    console.log('Appointment data (local test):', formData);
    
    // Show success message
    formMessage.addClass('alert alert-success')
        .html('<strong>Test Mode!</strong> In production, your appointment would be saved. Data: ' + JSON.stringify(formData));
    
    // Show success modal if it exists
    if ($('#successModal').length) {
        $('#successModal').modal('show');
    }
    
    // Reset form after 3 seconds
    setTimeout(() => {
        $('#appointmentForm')[0].reset();
        $('#appointment-time').empty().append('<option value="">Select Time</option>');
        formMessage.empty();
    }, 3000);
}