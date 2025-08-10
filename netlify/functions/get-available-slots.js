// Netlify Function获取可用时间槽
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

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

exports.handler = async (event, context) => {
    // 设置CORS headers
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, OPTIONS'
    };

    // 处理OPTIONS请求
    if (event.httpMethod === 'OPTIONS') {
        return {
            statusCode: 200,
            headers,
            body: ''
        };
    }

    // 只允许GET请求
    if (event.httpMethod !== 'GET') {
        return {
            statusCode: 405,
            headers,
            body: JSON.stringify({ error: 'Method not allowed' })
        };
    }

    try {
        // 获取查询参数中的日期
        const date = event.queryStringParameters?.date;
        
        if (!date) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'Date parameter is required' })
            };
        }

        // 检查环境变量
        if (!supabaseUrl || !supabaseKey) {
            console.error('Supabase credentials not configured');
            return {
                statusCode: 500,
                headers,
                body: JSON.stringify({ error: 'Server configuration error' })
            };
        }

        // 创建Supabase客户端
        const supabase = createClient(supabaseUrl, supabaseKey);

        // 查询该日期已预约的时间
        const { data: appointments, error } = await supabase
            .from('appointments')
            .select('time')
            .eq('date', date);

        if (error) {
            console.error('Supabase error:', error);
            return {
                statusCode: 500,
                headers,
                body: JSON.stringify({ error: 'Failed to fetch appointments' })
            };
        }

        // 获取已预约的时间槽
        const bookedSlots = appointments.map(apt => apt.time.substring(0, 5));

        // 获取该日期的排除时间槽
        const dateExclusions = excludedSlots[date] || [];

        // 计算可用时间槽
        const availableSlots = allTimeSlots.filter(slot => {
            // 排除已预约的
            if (bookedSlots.includes(slot)) return false;
            // 排除特定日期的
            if (dateExclusions.includes(slot)) return false;
            
            // 如果是今天，排除已过去的时间
            const selectedDate = new Date(date);
            const now = new Date();
            if (selectedDate.toDateString() === now.toDateString()) {
                const [hours, minutes] = slot.split(':').map(Number);
                const slotTime = hours * 60 + minutes;
                const currentTime = now.getHours() * 60 + now.getMinutes();
                if (slotTime <= currentTime) return false;
            }
            
            return true;
        });

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                date: date,
                availableSlots: availableSlots,
                bookedCount: bookedSlots.length
            })
        };

    } catch (error) {
        console.error('Server error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Failed to fetch available slots' })
        };
    }
};