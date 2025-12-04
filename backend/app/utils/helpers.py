import hashlib
import re
from datetime import datetime,timedelta
from typing import Dict,Any,List,Optional
import logging

logger=logging.getLogger(__name__)

def calculate_hash(content:str)->str:
    return hashlib.sha256(content.encode()).hexdigest()
    
def parse_circleci_datetime(date_str:str)->Optional[datetime]:
    if not dt_string:
        return None
    try:
        clean_dt=dt_string.replace("Z","+00:00")
        return datetime.fromisoformat(clean_dt)
    except ValueError:
        logger.warning(f"Invalid datetime format: {dt_string}")
        return None


def format_duration(seconds:int)->str:
    if seconds <60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes=seconds//60
        secs=seconds%60
        return f"{minutes} minutes {secs} seconds"
    else:
        hours=seconds//3600
        minutes=(seconds%3600)//60
        return f"{hours} hours {minutes} minutes"

def extract_project_info(project_slug:str)->Dict[str,Any]:

    parts = project_slug.split("/")
    if len(parts) >= 3:
        return {
            "vcs":parts[0],
            "organization":parts[1],
            "repository":parts[2]
        }
    return {}

def sanitize_branch_name(branch_name:str)->str:
    return re.sub(r'[^a-zA-Z0-9-]',"",branch)

def calculate_success_rate(total:int,successes:int)->float:
    if total == 0:
        return 0.0
    return round((successes/total)*100,2)

def get_time_range(days:int)->Dict[str,datetime]:
    end_date=datetime.now()
    start_date=end_date-timedelta(days=days)
    return {"start_date":start_date,"end_date":end_date}

def chunk_list(lst:List[Any],chunk_size:int)->List[List[Any]]:
   return [lst[i:i+chunk_size] for i in range(0,len(lst),chunk_size)]


def is_valid_project_slug(project_slug:str)->bool:
    pattern=r'^[a-z]+/[\w\-\.]+/[\w\-\.]+$'
    return bool(re.match(pattern,project_slug,re.IGNORECASE))

def extract_error_summary(log_content:str,max_lines:int=20)->str:
    if not log_content:
        return "No log content available"
    
    lines=log_content.split("\n")
    error_keywords=['error', 'failed', 'exception', 'fatal']

    error_lines=[]
    for line in lines:
        if any(keyword in line.lower() for keyword in error_keywords):
            error_lines.append(line.strip())
            if len(error_lines)>=max_lines:
                break
    if error_lines:
        return "\n".join(error_lines)
    else:
        return '\n'.join(lines[-max_lines:])


def calculate_percentile(values:List[float],percentile:float)->float:
    if not values:
        return 0.0
    sorted_data = sorted(values)
    index = int(len(sorted_data) * (percentile / 100))
    return sorted_data[min(index, len(sorted_data) - 1)]

def merge_dicts(*dicts:Dict)->Dict:
    result={}
    for d in dicts:
        result.update(d)
    return result


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, return default if division by zero"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length"""
    if len(text) <= max_length:
        return text
  
