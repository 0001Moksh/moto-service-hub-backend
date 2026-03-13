# Scaling Migration Checklist

**Date Started:** March 12, 2026  
**System:** Moto Service Hub - Booking Module  
**Target:** Support unlimited concurrent users  

---

## Phase 1: Database Setup ⏰ ~5 minutes

- [ ] **1.1** Open Supabase Dashboard
  - URL: https://supabase.com/dashboard
  - Project: moto-service-hub

- [ ] **1.2** Navigate to SQL Editor
  - Click: "SQL Editor" in left sidebar
  - Click: "New Query"

- [ ] **1.3** Copy migration SQL
  - File: `BOOKING_SESSION_MIGRATION.sql`
  - Copy entire contents

- [ ] **1.4** Execute Migration
  - Paste into Supabase SQL Editor
  - Click: "Run"
  - Expected: "Success"

- [ ] **1.5** Verify Table Creation
  - Go to: "Tables" in sidebar
  - Find: `booking_session` in list
  - Check columns exist: session_id, vehicle_id, current_step, expires_at

- [ ] **1.6** Verify Indexes
  - Run in SQL Editor:
    ```sql
    SELECT indexname FROM pg_indexes WHERE tablename='booking_session';
    ```
  - Should see: 3 indexes (vehicle_id, customer_id, expires_at)

---

## Phase 2: Code Review ⏰ ~10 minutes

- [ ] **2.1** Review New Router
  - File: `app/routers/booking_v2.py`
  - Lines: ~500 total
  - Key: Uses `session_id` (UUID) instead of `vehicle_id`

- [ ] **2.2** Review Updated Schemas
  - File: `app/schemas/booking.py`
  - Check: All requests/responses include `session_id`
  - Import: `from uuid import UUID`

- [ ] **2.3** Check main.py Update
  - File: `main.py`
  - Line: 8 should have: `from app.routers import booking_v2 as booking`

- [ ] **2.4** Read Documentation
  - File: `BOOKING_SCALABILITY_GUIDE.md`
  - File: `SCALING_QUICK_START.md`

---

## Phase 3: Local Testing ⏰ ~20 minutes

- [ ] **3.1** Start Development Server
  ```bash
  cd c:\Users\renuk\Projects\MOTO- SERVICE-HUB\backend
  uvicorn main:app --reload
  ```
  - Wait for: "Uvicorn running on http://127.0.0.1:8000"

- [ ] **3.2** Check Health Endpoint
  ```bash
  curl http://localhost:8000/health
  ```
  - Expected: `"status": "ok"`

- [ ] **3.3** Test Session Creation
  ```bash
  curl -X POST http://localhost:8000/api/booking/session/create \
    -H 'Content-Type: application/json' \
    -d '{"vehicle_id": 6, "customer_id": 1}'
  ```
  - Expected: UUID session_id returned

- [ ] **3.4** Run Full Test Suite
  ```bash
  # In new terminal
  python test_scalable_booking.py
  ```
  - Expected output: All 4 tests pass ✅

---

## Phase 4: Manual Testing ⏰ ~15 minutes

- [ ] **4.1** Test Single User Flow

  **Step 1: Create Session**
  ```bash
  SESSION_ID=$(curl -s -X POST http://localhost:8000/api/booking/session/create \
    -H 'Content-Type: application/json' \
    -d '{"vehicle_id": 6, "customer_id": 1}' | jq -r '.session_id')
  echo $SESSION_ID  # Save this
  ```

  **Step 2: Select Vehicle**
  ```bash
  curl -X POST http://localhost:8000/api/booking/step1-select-vehicle \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\": \"$SESSION_ID\", \"vehicle_id\": 6}"
  ```
  - Expected: `"success": true`

  **Step 3: Add Issues**
  ```bash
  curl -X POST http://localhost:8000/api/booking/step2-add-issue \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\": \"$SESSION_ID\", \"vehicle_id\": 6, \"issue_from_customer\": [\"Engine making noise\", \"Brake pads worn\"]}"
  ```
  - Expected: `"success": true`

  **Step 4: Select Shop**
  ```bash
  curl -X POST http://localhost:8000/api/booking/step3-select-shop \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\": \"$SESSION_ID\", \"vehicle_id\": 6, \"shop_id\": 2}"
  ```
  - Expected: `"success": true`

  **Step 5: Book Time Slot**
  ```bash
  curl -X POST http://localhost:8000/api/booking/step4-book-timeslot \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\": \"$SESSION_ID\", \"vehicle_id\": 6, \"shop_id\": 2, \"issue_from_customer\": [\"Engine making noise\"], \"service_at\": \"2026-03-15T10:00:00\", \"booking_trust\": false}"
  ```
  - Expected: Booking ID returned

- [ ] **4.2** Test Session Retrieval
  ```bash
  curl -X GET http://localhost:8000/api/booking/session/$SESSION_ID
  ```
  - Expected: Session details including current_step

---

## Phase 5: Database Verification ⏰ ~10 minutes

- [ ] **5.1** Verify Data in Database
  ```bash
  # In Supabase SQL Editor, run:
  SELECT session_id, customer_id, vehicle_id, current_step, 
         status, created_at
  FROM booking_session
  ORDER BY created_at DESC
  LIMIT 5;
  ```
  - Expected: Rows from your test bookings

- [ ] **5.2** Verify Bookings Table
  ```bash
  SELECT booking_id, vehicle_id, shop_id, status, created_at
  FROM booking
  ORDER BY booking_id DESC
  LIMIT 3;
  ```
  - Expected: Bookings created during testing

- [ ] **5.3** Check Session Status
  ```bash
  SELECT 
    COUNT(*) as total,
    status,
    COUNT(CASE WHEN current_step >= 4 THEN 1 END) as completed
  FROM booking_session
  GROUP BY status;
  ```
  - Expected: Sessions tracked by status

---

## Phase 6: Edge Case Testing ⏰ ~10 minutes

- [ ] **6.1** Test Invalid Session ID
  ```bash
  curl -X GET http://localhost:8000/api/booking/session/invalid-uuid
  ```
  - Expected: `"detail": "Booking session not found or expired"`

- [ ] **6.2** Test Out-of-Order Steps
  ```bash
  # Try step3 without doing step2 first
  curl -X POST http://localhost:8000/api/booking/step3-select-shop \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\": \"$SESSION_ID\", \"vehicle_id\": 6, \"shop_id\": 2}"
  ```
  - Expected: `"detail": "Please add issue description first"`

- [ ] **6.3** Test Expired Session
  ```bash
  # In Supabase, manually update:
  UPDATE booking_session 
  SET expires_at = NOW() - INTERVAL '1 hour'
  WHERE session_id = '$SESSION_ID';
  
  # Then try to use it:
  curl -X GET http://localhost:8000/api/booking/session/$SESSION_ID
  ```
  - Expected: `"detail": "Booking session has expired"`

- [ ] **6.4** Test Concurrent Operations
  ```bash
  # Run test_scalable_booking.py again
  python test_scalable_booking.py
  ```
  - Expected: All 5 concurrent users complete without conflicts ✅

---

## Phase 7: Performance Testing ⏰ ~15 minutes

- [ ] **7.1** Load Test: 10 Concurrent Users
  ```python
  # Modify test_scalable_booking.py:
  test_concurrent_bookings(10)
  ```
  - Expected: All 10 complete successfully
  - Check time taken: Should be < 30 seconds

- [ ] **7.2** Load Test: 50 Concurrent Users
  ```python
  test_concurrent_bookings(50)
  ```
  - Expected: All 50 complete successfully
  - Check time taken: Should be < 2 minutes

- [ ] **7.3** Monitor Database Performance
  ```bash
  # In Supabase, check logs:
  # Dashboard → Monitoring → Query Performance
  # Look for any slow queries on booking_session
  ```
  - Expected: < 1ms average query time with indexes

---

## Phase 8: Documentation Review ⏰ ~10 minutes

- [ ] **8.1** Read Quick Start Guide
  - File: `SCALING_QUICK_START.md`
  - Ensure you understand: Session creation + step flow

- [ ] **8.2** Read Full Documentation
  - File: `BOOKING_SCALABILITY_GUIDE.md`
  - Sections: Architecture, API Examples, Troubleshooting

- [ ] **8.3** Share with Team
  - Commit all files
  - Create PR with documentation
  - PR description: "Scale booking system to support unlimited concurrent users"

---

## Phase 9: Deploy to Staging ⏰ ~20 minutes

- [ ] **9.1** Run Migration on Staging Database
  - Run BOOKING_SESSION_MIGRATION.sql
  - Verify table created

- [ ] **9.2** Deploy Code to Staging
  ```bash
  git add .
  git commit -m "Scale booking system: use sessions instead of in-memory storage"
  git push origin staging
  ```

- [ ] **9.3** Run Test Suite on Staging
  ```bash
  python test_scalable_booking.py
  ```
  - Expected: All tests pass ✅

- [ ] **9.4** Verify Production Database Not Affected
  - Check production `booking_session` table does NOT exist yet
  - Verify production bookings still work

---

## Phase 10: Deploy to Production ⏰ ~30 minutes

- [ ] **10.1** Backup Production Database
  ```bash
  # In Supabase dashboard:
  # Settings → Backups → Create Manual Backup
  ```

- [ ] **10.2** Schedule Maintenance Window
  - Notify users: "Booking system upgrade - 5 min downtime"

- [ ] **10.3** Run Migration on Production
  - Execute BOOKING_SESSION_MIGRATION.sql in production database
  - Verify: booking_session table created with data

- [ ] **10.4** Deploy Code to Production
  ```bash
  git push origin main
  # Or deploy via your CI/CD pipeline
  ```

- [ ] **10.5** Health Check
  ```bash
  curl https://your-production-api.com/health
  ```
  - Expected: `"status": "ok"`

- [ ] **10.6** Smoke Test
  ```bash
  # Run quick manual test of all 4 steps
  # Using production API endpoint
  ```

- [ ] **10.7** Monitor Production Logs
  ```bash
  # Watch logs for errors:
  tail -f logs/app.log | grep booking_session
  ```
  - Expected: No ERRORs, only INFO logs

- [ ] **10.8** Update Status
  - Announce: "Booking system upgrade complete"
  - Users can now book concurrently without issues ✅

---

## Post-Deployment ⏰ Ongoing

- [ ] **11.1** Monitor Active Sessions
  ```sql
  -- Run daily:
  SELECT COUNT(*) FROM booking_session 
  WHERE status='in_progress' AND expires_at > now();
  ```

- [ ] **11.2** Setup Auto-Cleanup (Optional)
  ```sql
  -- Connect to Supabase PostgreSQL extensions
  CREATE EXTENSION IF NOT EXISTS pg_cron;
  
  SELECT cron.schedule('cleanup-sessions', '0 * * * *', 
    'DELETE FROM booking_session WHERE expires_at < now()');
  ```

- [ ] **11.3** Track Zero Conflicts
  - Monitor error logs
  - Expected: ZERO "race condition" or "conflict" errors

- [ ] **11.4** Performance Baseline
  ```bash
  # Each week, run:
  python test_scalable_booking.py
  # Track: Completion time, success rate (should be 100%)
  ```

---

## Rollback Plan (If Needed)

If you encounter issues:

1. **Stop new sessions** (remove session creation endpoint)
2. **Revert main.py** to use old booking router
3. **Restore database backup** (Supabase → Backups → Restore)
4. **Restart server** with old code

```bash
# Revert to old router:
git checkout HEAD~1 main.py
git push
uvicorn main:app --reload
```

---

## Sign-Off

- [ ] **All Tests Passed:** ✅ Yes / ❌ No
- [ ] **Database Verified:** ✅ Yes / ❌ No
- [ ] **Documentation Reviewed:** ✅ Yes / ❌ No
- [ ] **Deployed to Production:** ✅ Yes / ❌ No

**Migration Completed:** __________  
**Reviewed By:** __________  
**Status:** ✅ COMPLETE / ⚠️ PENDING / ❌ FAILED

---

**Success Criteria:**
- ✅ Booking system supports 1000+ concurrent users
- ✅ Zero conflicts between sessions
- ✅ Data persists across server restarts
- ✅ All tests pass (single + concurrent)
- ✅ Database verified with proper schema
