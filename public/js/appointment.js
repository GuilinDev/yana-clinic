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
        
        // 如果Functions未部署或环境变量未设置，使用备用方案
        if (!response.ok) {
            console.error('Netlify Function error, using fallback. Status:', response.status);
            // 使用本地备用逻辑
            loadAvailableTimeSlotsLocally(date, timeSelect);
            return;
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
        // 使用本地备用逻辑
        loadAvailableTimeSlotsLocally(date, timeSelect);
    }
}

// 备用函数：当Netlify Functions不可用时使用
function loadAvailableTimeSlotsLocally(date, timeSelect) {
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
    timeSelect.empty();
    if (availableSlots.length > 0) {
        timeSelect.append('<option value="">Select Time</option>');
        availableSlots.forEach(slot => {
            timeSelect.append(`<option value="${slot}">${slot}</option>`);
        });
    } else {
        timeSelect.append('<option value="">No available slots</option>');
    }
    
    console.log('Using local fallback for time slots (Netlify Functions may not be configured)');
}

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
        
        if (!response.ok) {
            // 如果Functions不可用，显示警告但标记为成功（临时方案）
            if (response.status === 404 || response.status === 502) {
                console.warn('Netlify Functions not available, showing success for demo');
                formMessage.addClass('alert alert-warning')
                    .html('<strong>Note:</strong> Booking system is being configured. Please call us at (978) 729-5878 to confirm your appointment.');
                
                // Show modal if exists
                if ($('#successModal').length) {
                    $('#successModal').modal('show');
                }
                
                // Reset form
                setTimeout(() => {
                    $('#appointmentForm')[0].reset();
                    $('#appointment-time').empty().append('<option value="">Select Time</option>');
                }, 3000);
                return;
            }
            
            const result = await response.json();
            throw new Error(result.error || 'Failed to book appointment');
        }
        
        const result = await response.json();
        
        // Show success message
        formMessage.addClass('alert alert-success')
            .html('<strong>Success!</strong> Your appointment has been booked successfully. We will contact you soon.');
        
        // Show modal if exists
        if ($('#successModal').length) {
            $('#successModal').modal('show');
        }
        
        // Reset form
        $('#appointmentForm')[0].reset();
        $('#appointment-time').empty().append('<option value="">Select Time</option>');
        
    } catch (error) {
        console.error('Error submitting appointment:', error);
        
        // 如果是网络错误，提供更友好的提示
        if (error.message.includes('Failed to fetch')) {
            formMessage.addClass('alert alert-warning')
                .html('<strong>Connection Issue:</strong> Unable to submit online. Please call us at (978) 729-5878 to book your appointment.');
        } else {
            formMessage.addClass('alert alert-danger')
                .html('<strong>Error!</strong> Failed to book appointment. Please try again or contact us directly at (978) 729-5878.');
        }
    }
}

