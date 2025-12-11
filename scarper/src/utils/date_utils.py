import calendar
from datetime import timedelta

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return sourcedate.replace(year=year, month=month, day=day)

def generate_date_ranges(start_date, end_date):
    current_start = start_date
    ranges = []
    
    # monthly partition logic
    while current_start < end_date:
       
        next_start = add_months(current_start, 1)
        current_end = next_start - timedelta(days=1)

        if current_end > end_date:
            current_end = end_date
        
        if current_start > end_date:
            break

        ranges.append((current_start, current_end))
        current_start = next_start
        
    return ranges
