-- Supabase schema for appointments table
-- Run this in your Supabase SQL editor

-- Create appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(254) NOT NULL,
    service VARCHAR(100) DEFAULT 'Not specified',
    date DATE NOT NULL,
    time TIME NOT NULL,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX idx_appointments_date ON appointments(date);
CREATE INDEX idx_appointments_date_time ON appointments(date, time);

-- Enable Row Level Security (RLS)
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;

-- Create policy for inserting appointments (anyone can book)
CREATE POLICY "Anyone can insert appointments" ON appointments
    FOR INSERT 
    WITH CHECK (true);

-- Create policy for reading appointments (only authenticated users/admin)
-- You can modify this based on your needs
CREATE POLICY "Authenticated users can read appointments" ON appointments
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- Optional: Create a function to automatically update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE
    ON appointments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Optional: Create a view for available time slots
CREATE OR REPLACE VIEW available_slots AS
SELECT 
    date,
    COUNT(*) as booked_count,
    array_agg(time ORDER BY time) as booked_times
FROM appointments
WHERE date >= CURRENT_DATE
GROUP BY date;