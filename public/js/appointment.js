// Supabase configuration
// 请替换为你的实际Supabase项目URL和匿名密钥
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';

// Initialize Supabase client
let supabase;
if (typeof window !== 'undefined' && window.supabase) {
    supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}

// Available time slots
const timeSlots = [
    '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
    '11:00', '11:30', '13:00', '13:30', '14:00', '14:30',
    '15:00', '15:30', '16:00', '16:30'
];

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
        // Skip some specific time slots (from original Django logic)
        const excludedSlots = getExcludedSlots(date);
        
        // Get booked appointments from Supabase
        let bookedSlots = [];
        if (supabase) {
            const { data, error } = await supabase
                .from('appointments')
                .select('time')
                .eq('date', date);
            
            if (!error && data) {
                bookedSlots = data.map(apt => apt.time.substring(0, 5)); // Format: HH:MM
            }
        }
        
        // Filter available slots
        timeSelect.empty();
        timeSelect.append('<option value="">Select Time</option>');
        
        const selectedDateTime = new Date(date);
        const now = new Date();
        const isToday = selectedDateTime.toDateString() === now.toDateString();
        const currentTime = now.getHours() * 60 + now.getMinutes();
        
        timeSlots.forEach(slot => {
            // Skip if slot is excluded
            if (excludedSlots.includes(slot)) {
                return;
            }
            
            // Skip if slot is already booked
            if (bookedSlots.includes(slot)) {
                return;
            }
            
            // Skip past time slots for today
            if (isToday) {
                const [hours, minutes] = slot.split(':').map(Number);
                const slotTime = hours * 60 + minutes;
                if (slotTime <= currentTime) {
                    return;
                }
            }
            
            timeSelect.append(`<option value="${slot}">${slot}</option>`);
        });
        
        if (timeSelect.find('option').length === 1) {
            timeSelect.empty();
            timeSelect.append('<option value="">No available slots</option>');
        }
    } catch (error) {
        console.error('Error loading time slots:', error);
        timeSelect.empty();
        timeSelect.append('<option value="">Error loading slots</option>');
    }
}

// Get excluded time slots based on date (from original Django logic)
function getExcludedSlots(date) {
    const excludedSlots = [];
    
    // 2024-12-31: Exclude 11:00, 11:30, 15:00, 15:30
    if (date === '2024-12-31') {
        excludedSlots.push('11:00', '11:30', '15:00', '15:30');
    }
    // 2025-01-02: Exclude 09:30, 10:00, 10:30, 11:00, 13:00, 13:30, 14:00, 14:30
    else if (date === '2025-01-02') {
        excludedSlots.push('09:30', '10:00', '10:30', '11:00', '13:00', '13:30', '14:00', '14:30');
    }
    // 2025-01-03: Exclude 08:00, 08:30, 09:00, 09:30, 10:00, 10:30, 13:00, 13:30, 14:00
    else if (date === '2025-01-03') {
        excludedSlots.push('08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '13:00', '13:30', '14:00');
    }
    // 2025-01-07: Exclude 09:30, 10:00, 10:30, 11:00, 13:00, 13:30, 14:00, 14:30
    else if (date === '2025-01-07') {
        excludedSlots.push('09:30', '10:00', '10:30', '11:00', '13:00', '13:30', '14:00', '14:30');
    }
    // 2025-01-08: Exclude 09:00, 09:30, 10:00, 10:30, 11:00, 11:30, 14:00, 14:30, 15:00, 15:30
    else if (date === '2025-01-08') {
        excludedSlots.push('09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30', '15:00', '15:30');
    }
    // 2025-01-09: Exclude 09:30, 10:00, 10:30, 11:00, 13:00, 13:30, 14:00, 14:30
    else if (date === '2025-01-09') {
        excludedSlots.push('09:30', '10:00', '10:30', '11:00', '13:00', '13:30', '14:00', '14:30');
    }
    // 2025-01-10: Exclude 08:00, 08:30, 09:00, 09:30, 10:00, 10:30, 13:00, 13:30, 14:00, 14:30
    else if (date === '2025-01-10') {
        excludedSlots.push('08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '13:00', '13:30', '14:00', '14:30');
    }
    
    return excludedSlots;
}

// Submit appointment to Supabase
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
        time: $('#appointment-time').val() + ':00', // Add seconds for proper time format
        message: $('#message').val() || null,
        created_at: new Date().toISOString()
    };
    
    try {
        if (!supabase) {
            throw new Error('Supabase is not configured. Please set up your Supabase credentials.');
        }
        
        // Insert appointment into Supabase
        const { data, error } = await supabase
            .from('appointments')
            .insert([formData])
            .select();
        
        if (error) {
            throw error;
        }
        
        // Show success message
        formMessage.addClass('alert alert-success')
            .html('<strong>Success!</strong> Your appointment has been booked successfully. We will contact you soon.');
        
        // Reset form
        $('#appointmentForm')[0].reset();
        $('#appointment-time').empty().append('<option value="">Select Time</option>');
        
        // Send confirmation email (optional - can be done via Supabase Edge Functions or Netlify Functions)
        // await sendConfirmationEmail(formData);
        
    } catch (error) {
        console.error('Error submitting appointment:', error);
        formMessage.addClass('alert alert-danger')
            .html('<strong>Error!</strong> Failed to book appointment. Please try again or contact us directly.');
    }
}

// Optional: Send confirmation email via Netlify Function
async function sendConfirmationEmail(appointmentData) {
    try {
        const response = await fetch('/.netlify/functions/send-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(appointmentData)
        });
        
        if (!response.ok) {
            console.error('Failed to send confirmation email');
        }
    } catch (error) {
        console.error('Error sending email:', error);
    }
}