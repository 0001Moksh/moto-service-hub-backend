-- ==================== BOOKING SESSION TABLE ====================
-- This table tracks the progress of each user's booking workflow
-- Supports unlimited concurrent users without conflicts

CREATE TABLE IF NOT EXISTS public.booking_session (
  session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id BIGINT,
  vehicle_id BIGINT NOT NULL,
  shop_id BIGINT,
  issue_from_customer TEXT[] DEFAULT '{}',
  current_step INTEGER DEFAULT 1 CHECK (current_step >= 1 AND current_step <= 4),
  status VARCHAR DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  expires_at TIMESTAMP DEFAULT (now() + INTERVAL '24 hours'),
  CONSTRAINT fk_session_vehicle FOREIGN KEY (vehicle_id) REFERENCES public.vehicle(vehicle_id) ON DELETE CASCADE,
  CONSTRAINT fk_session_shop FOREIGN KEY (shop_id) REFERENCES public.shop(shop_id) ON DELETE SET NULL
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_booking_session_vehicle_id ON public.booking_session(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_booking_session_customer_id ON public.booking_session(customer_id);
CREATE INDEX IF NOT EXISTS idx_booking_session_expires_at ON public.booking_session(expires_at);

-- Create trigger to auto-update updated_at timestamp
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

-- Optional: Create job to clean up expired sessions (run via database cron)
-- SELECT cron.schedule('cleanup-expired-booking-sessions', '0 * * * *', 
--   'DELETE FROM public.booking_session WHERE expires_at < now()');
