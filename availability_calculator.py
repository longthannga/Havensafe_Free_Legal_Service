from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import parse_hours

def next_available_slot(org_schedule, org_name, phone):
    """Find next available slot for an organization"""
    tz = ZoneInfo('America/Los_Angeles')
    now = datetime.now(tz)
    current_time = now.time()
    current_date = now.date()
    
    # Check next 7 days
    for day_offset in range(0, 8):
        check_date = current_date + timedelta(days=day_offset)
        weekday = check_date.strftime('%A')
        
        if weekday in org_schedule:
            for slot in org_schedule[weekday]:
                slot_start = slot['start']
                slot_end = slot['end']
                
                # Create datetime objects for comparison
                slot_start_dt = datetime.combine(check_date, slot_start).astimezone(tz)
                slot_end_dt = datetime.combine(check_date, slot_end).astimezone(tz)
                
                # Check if slot is in future
                if now < slot_end_dt:
                    return {
                        'org': org_name,
                        'phone': phone,
                        'time': slot_start_dt.strftime('%-I:%M%p').lower().replace('am', 'am').replace('pm', 'pm'),
                        'day': weekday,
                        'datetime': slot_start_dt,
                        'type': slot['type']  # Include service type
                    }
    return None

def generate_recommendations(data):
    """Generate availability recommendations based on scraped data"""
    tz = ZoneInfo('America/Los_Angeles')
    now = datetime.now(tz)
    current_time = now.time()
    current_day = now.strftime('%A')
    
    # Parse schedules for all organizations
    org_schedules = {}
    for i in range(len(data['name'])):
        name = data['name'][i]
        hours_text = data['office hours'][i] or ""
        
        if "Law Foundation" in name:
            org_schedules[name] = parse_hours.parse_law_foundation(hours_text)
        elif "Asian Law Alliance" in name:
            org_schedules[name] = parse_hours.parse_asian_law_alliance(hours_text)
        elif "Bay Area Legal Aid" in name:
            org_schedules[name] = parse_hours.parse_bay_legal_aid(hours_text)
        elif "Senior Adults" in name:
            org_schedules[name] = parse_hours.parse_sala(hours_text)
    
    # Find next available slots
    recommendations = []
    for name, schedule in org_schedules.items():
        if "Senior Adults" not in name:  # Exclude SALA from recommendations
            phone = next((p for i, p in enumerate(data['phone']) if data['name'][i] == name), "")
            if slot := next_available_slot(schedule, name, phone):
                recommendations.append(slot)
    
    # Sort by next available time
    recommendations.sort(key=lambda x: x['datetime'])
    
    # Format recommendations
    if recommendations:
        message = "Unless you are eligible for SALA (age 60+), here are the next/current available legal advice line(s):\n"
        for rec in recommendations:
            # Generate appropriate note based on service type
            if rec['type'] == 'phone':
                note = " (phone only)"
            elif rec['type'] == 'walk-in':
                note = " (walk-ins accepted)"
            else:
                note = ""
            
            message += f"{rec['time']} on {rec['day']}, {rec['org']}, {rec['phone']}{note}\n"
        return message.strip()
    return "No available services found. Please check back during business hours."