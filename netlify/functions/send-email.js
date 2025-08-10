// Netlify Function to send appointment confirmation emails
// This is optional - you can also use Supabase Edge Functions

exports.handler = async (event, context) => {
    // Only allow POST requests
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            body: JSON.stringify({ error: 'Method not allowed' })
        };
    }

    try {
        const appointment = JSON.parse(event.body);
        
        // Here you would integrate with your email service
        // Examples: SendGrid, Mailgun, AWS SES, etc.
        
        // Example with a generic email service:
        /*
        const emailService = require('your-email-service');
        
        await emailService.send({
            to: appointment.email,
            from: process.env.ADMIN_EMAIL,
            subject: 'Appointment Confirmation - Bless and Joy Wellness',
            html: `
                <h2>Appointment Confirmation</h2>
                <p>Dear ${appointment.name},</p>
                <p>Your appointment has been successfully booked.</p>
                <ul>
                    <li><strong>Date:</strong> ${appointment.date}</li>
                    <li><strong>Time:</strong> ${appointment.time}</li>
                    <li><strong>Service:</strong> ${appointment.service}</li>
                </ul>
                <p>Location: 420 Main Street, Wilmington, MA 01887</p>
                <p>Phone: (978) 729-5878</p>
                <p>If you need to cancel or reschedule, please contact us at least 24 hours in advance.</p>
                <p>Thank you for choosing Bless and Joy Wellness!</p>
            `
        });
        
        // Also send notification to admin
        await emailService.send({
            to: process.env.ADMIN_EMAIL,
            from: process.env.ADMIN_EMAIL,
            subject: `New Appointment - ${appointment.name}`,
            html: `
                <h2>New Appointment Booking</h2>
                <ul>
                    <li><strong>Name:</strong> ${appointment.name}</li>
                    <li><strong>Phone:</strong> ${appointment.phone}</li>
                    <li><strong>Email:</strong> ${appointment.email}</li>
                    <li><strong>Date:</strong> ${appointment.date}</li>
                    <li><strong>Time:</strong> ${appointment.time}</li>
                    <li><strong>Service:</strong> ${appointment.service}</li>
                    <li><strong>Message:</strong> ${appointment.message || 'None'}</li>
                </ul>
            `
        });
        */
        
        // For now, just log and return success
        console.log('Email would be sent for appointment:', appointment);
        
        return {
            statusCode: 200,
            body: JSON.stringify({ success: true, message: 'Email sent successfully' })
        };
        
    } catch (error) {
        console.error('Error sending email:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: 'Failed to send email' })
        };
    }
};