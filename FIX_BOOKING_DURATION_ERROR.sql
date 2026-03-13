-- FIX: Remove problematic trigger causing "record "new" has no field "duration"" error
-- This trigger was likely trying to calculate duration on booking creation
-- but the booking table doesn't have a duration field (that's in the service table)

-- Drop the problematic trigger if it exists
DROP TRIGGER IF EXISTS set_booking_duration ON public.booking;
DROP FUNCTION IF EXISTS set_booking_duration_func();

-- Also drop booking_session triggers if they exist and are causing issues
DROP TRIGGER IF EXISTS booking_session_update_timestamp ON public.booking_session;
DROP FUNCTION IF EXISTS update_booking_session_timestamp();

-- Recreate the booking_session trigger properly
CREATE OR REPLACE FUNCTION update_booking_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER booking_session_update_timestamp
BEFORE UPDATE ON public.booking_session
FOR EACH ROW
EXECUTE FUNCTION update_booking_session_timestamp();

-- Verify the booking table structure - it should NOT have duration
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'booking';
