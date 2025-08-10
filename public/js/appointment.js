// 使用Netlify Functions作为安全的API代理
// 不再需要直接暴露Supabase凭据

// Initialize date picker
$(document).ready(function() {
    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    $('#appointment-date').attr('min', today);
    
    // Handle date selection
    $('#appointment-date').on('change', async function() {
        const selectedDate = $(this).val();
        if (selectedDate) {
            await loadAvailableTimeSlots(selectedDate);
        }
    });
    
    // Handle form submission
    $('#appointmentForm').on('submit', async function(e) {
        e.preventDefault();
        await submitAppointment();
    });
});

// Load available time slots for selected date
async function loadAvailableTimeSlots(date) {
    const timeSelect = $('#appointment-time');
    timeSelect.empty();
    timeSelect.append('<option value="">Loading...</option>');
    
    try {
        // 调用Netlify Function获取可用时间槽
        const response = await fetch(`/.netlify/functions/get-available-slots?date=${date}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch available slots');
        }
        
        const data = await response.json();
        
        // 更新时间选择器
        timeSelect.empty();
        
        if (data.availableSlots && data.availableSlots.length > 0) {
            timeSelect.append('<option value="">Select Time</option>');
            data.availableSlots.forEach(slot => {
                timeSelect.append(`<option value="${slot}">${slot}</option>`);
            });
        } else {
            timeSelect.append('<option value="">No available slots</option>');
        }
        
    } catch (error) {
        console.error('Error loading time slots:', error);
        timeSelect.empty();
        timeSelect.append('<option value="">Error loading slots</option>');
    }
}

// 注意：时间排除逻辑已经移到Netlify Function中处理

// Submit appointment via Netlify Function
async function submitAppointment() {
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
    
    try {
        // 调用Netlify Function提交预约
        const response = await fetch('/.netlify/functions/book-appointment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to book appointment');
        }
        
        // Show success message
        formMessage.addClass('alert alert-success')
            .html('<strong>Success!</strong> Your appointment has been booked successfully. We will contact you soon.');
        
        // Reset form
        $('#appointmentForm')[0].reset();
        $('#appointment-time').empty().append('<option value="">Select Time</option>');
        
    } catch (error) {
        console.error('Error submitting appointment:', error);
        formMessage.addClass('alert alert-danger')
            .html('<strong>Error!</strong> Failed to book appointment. Please try again or contact us directly.');
    }
}

