import re
from datetime import time, datetime

def parse_time(time_str):
    """Parse various time formats into time objects"""
    time_str = time_str.strip().lower().replace(' ', '')
    if not time_str:
        return None
    
    # Handle formats: 9:30am, 1:00pm, 13:00, 9am, etc.
    formats = [
        (r"^(\d{1,2}):(\d{2})([ap]m)$", lambda m: (int(m[1]), int(m[2]), m[3])),  # 1:30pm
        (r"^(\d{1,2})([ap]m)$", lambda m: (int(m[1]), 0, m[2])),                  # 1pm
        (r"^(\d{1,2}):(\d{2})$", lambda m: (int(m[1]), int(m[2]), None)),         # 13:00
        (r"^(\d{1,2})$", lambda m: (int(m[1]), 0, None))                          # 13
    ]
    
    for pattern, handler in formats:
        match = re.match(pattern, time_str)
        if match:
            hour, minute, period = handler(match)
            
            # Convert 12-hour format to 24-hour
            if period:
                if period == 'pm' and hour < 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
            elif hour < 12:  # Assume PM if no period and hour < 12
                hour += 12
                
            # Handle 24-hour rollover
            if hour >= 24:
                hour = 23
                minute = 59
                
            return time(hour, minute)
    
    return None

def parse_daily_hours(day_block):
    """Parse multiple time slots from a day's description"""
    slots = []
    # Find all time ranges in the text
    time_ranges = re.findall(
        r'(\d{1,2}(?::\d{2})?\s*[ap]?m?|\d{1,2}(?::\d{2})?)\s*[-–—to]+\s*(\d{1,2}(?::\d{2})?\s*[ap]?m?|\d{1,2}(?::\d{2})?)',
        day_block, 
        re.IGNORECASE
    )
    
    # Determine service type based on content
    service_type = 'general'
    if 'no walk-ins' in day_block.lower() or 'phone only' in day_block.lower():
        service_type = 'phone'
    elif 'walk-in' in day_block.lower():
        service_type = 'walk-in'
    
    for start_str, end_str in time_ranges:
        start_time = parse_time(start_str)
        end_time = parse_time(end_str)
        if start_time and end_time:
            slots.append({
                'start': start_time,
                'end': end_time,
                'type': service_type
            })
    return slots

def parse_law_foundation(hours_text):
    """Parse Law Foundation hours with improved regex patterns"""
    parsed = {}
    
    # Extract phone hours section
    phone_match = re.search(
        r"Phone Intake Hours:(.*?)(?=WALK-IN HOURS:|\Z)", 
        hours_text, 
        re.DOTALL | re.IGNORECASE
    )
    
    if phone_match:
        phone_text = phone_match.group(1)
        # Parse Monday phone hours
        monday_match = re.search(r"Monday\s*([\d\sapm:–—\-]+)", phone_text, re.IGNORECASE)
        if monday_match:
            parsed['Monday'] = parse_daily_hours(monday_match.group(0))
            # Explicitly mark as phone service
            for slot in parsed['Monday']:
                slot['type'] = 'phone'
    
    # Extract walk-in hours section - Updated to handle "Every Thursday from 1pm until appointments are full"
    walkin_match = re.search(
        r"WALK-IN HOURS:(.*)", 
        hours_text, 
        re.DOTALL | re.IGNORECASE
    )
    
    if walkin_match:
        walkin_text = walkin_match.group(1)
        # Look for Thursday walk-in pattern - handle "Every Thursday from 1pm until appointments are full"
        thursday_pattern = r"(?:Every\s+)?Thursday\s+from\s+(\d{1,2}(?::\d{2})?\s*[ap]m)(?:\s+until\s+appointments\s+are\s+full)?|Thursday\s*([\d\sapm:–—\-]+)"
        thursday_match = re.search(thursday_pattern, walkin_text, re.IGNORECASE)
        
        if thursday_match:
            if thursday_match.group(1):  # "from 1pm until appointments are full" format
                start_time = parse_time(thursday_match.group(1))
                if start_time:
                    # Set end time to 5pm as a reasonable closing time
                    parsed['Thursday'] = [{
                        'start': start_time,
                        'end': time(17, 0),  # 5:00 PM
                        'type': 'walk-in'
                    }]
            elif thursday_match.group(2):  # Regular time range format
                parsed['Thursday'] = parse_daily_hours(thursday_match.group(0))
                # Explicitly mark as walk-in service
                for slot in parsed['Thursday']:
                    slot['type'] = 'walk-in'
    
    return parsed

def parse_asian_law_alliance(hours_text):
    """Parse Asian Law Alliance hours"""
    parsed = {}
    # Process each day's entry
    day_pattern = r"(Monday|Tuesday|Wednesday|Thursday|Friday):\s*([^\n]+)"
    for day_match in re.finditer(day_pattern, hours_text, re.IGNORECASE):
        day, times = day_match.groups()
        parsed[day] = parse_daily_hours(times)
    return parsed

def parse_bay_legal_aid(hours_text):
    """Parse Bay Area Legal Aid hours"""
    parsed = {}
    # Process each day's entry
    for line in hours_text.split('\n'):
        if ':' in line and 'closed' not in line.lower():
            day_part, times = line.split(':', 1)
            day_match = re.search(r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)", day_part, re.IGNORECASE)
            if day_match:
                day = day_match.group(1)
                parsed[day] = parse_daily_hours(times)
    return parsed

def parse_sala(hours_text):
    """Parse SALA hours (simple weekday coverage)"""
    return {
        'Monday': [{'start': time(9), 'end': time(17), 'type': 'general'}],
        'Tuesday': [{'start': time(9), 'end': time(17), 'type': 'general'}],
        'Wednesday': [{'start': time(9), 'end': time(17), 'type': 'general'}],
        'Thursday': [{'start': time(9), 'end': time(17), 'type': 'general'}],
        'Friday': [{'start': time(9), 'end': time(17), 'type': 'general'}]
    }

def parse_pro_bono_project(hours_text):
    """Parse Pro Bono Project hours - Monday, Wednesday & Friday 8:30am-4:30pm"""
    parsed = {}
    
    # Look for the specific pattern "Monday, Wednesday & Friday 8:30am-4:30pm"
    pattern = r"(?:Monday|Wednesday|Friday).*?(\d{1,2}:\d{2}[ap]m)\s*[-–—]\s*(\d{1,2}:\d{2}[ap]m)"
    match = re.search(pattern, hours_text, re.IGNORECASE)
    
    if match:
        start_time = parse_time(match.group(1))
        end_time = parse_time(match.group(2))
        
        if start_time and end_time:
            # Add the same hours for Monday, Wednesday, and Friday
            for day in ['Monday', 'Wednesday', 'Friday']:
                parsed[day] = [{
                    'start': start_time,
                    'end': end_time,
                    'type': 'phone'  # Pro Bono Project uses telephone hours
                }]
    else:
        # Fallback: default hours if pattern not found
        default_start = time(8, 30)  # 8:30 AM
        default_end = time(16, 30)   # 4:30 PM
        
        for day in ['Monday', 'Wednesday', 'Friday']:
            parsed[day] = [{
                'start': default_start,
                'end': default_end,
                'type': 'phone'
            }]
    
    return parsed