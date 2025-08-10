// Netlify Function作为API代理，安全地处理Supabase调用
const { createClient } = require('@supabase/supabase-js');

// 这些环境变量在Netlify后台设置，不会暴露给客户端
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

exports.handler = async (event, context) => {
    // 设置CORS headers
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    };

    // 处理OPTIONS请求（CORS预检）
    if (event.httpMethod === 'OPTIONS') {
        return {
            statusCode: 200,
            headers,
            body: ''
        };
    }

    // 只允许POST请求
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            headers,
            body: JSON.stringify({ error: 'Method not allowed' })
        };
    }

    try {
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

        // 解析请求数据
        const appointmentData = JSON.parse(event.body);

        // 验证必填字段
        if (!appointmentData.name || !appointmentData.phone || !appointmentData.email || 
            !appointmentData.date || !appointmentData.time) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'Missing required fields' })
            };
        }

        // 格式化数据
        const formattedData = {
            name: appointmentData.name,
            phone: appointmentData.phone,
            email: appointmentData.email,
            service: appointmentData.service || 'Not specified',
            date: appointmentData.date,
            time: appointmentData.time + ':00', // 添加秒数
            message: appointmentData.message || null,
            created_at: new Date().toISOString()
        };

        // 插入到Supabase
        const { data, error } = await supabase
            .from('appointments')
            .insert([formattedData])
            .select();

        if (error) {
            console.error('Supabase error:', error);
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: error.message })
            };
        }

        // 成功响应
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({ 
                success: true, 
                message: 'Appointment booked successfully',
                data: data[0]
            })
        };

    } catch (error) {
        console.error('Server error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Failed to book appointment' })
        };
    }
};