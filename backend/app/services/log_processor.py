import re
import logging
from typing import Dict, List, Any
from collections import Counter

logger = logging.getLogger(__name__)


class LogProcessor:
    """Process and extract features from build logs"""
    
    # Common error patterns
    ERROR_PATTERNS = [
        r'error:',
        r'exception:',
        r'failed',
        r'fatal:',
        r'traceback',
        r'segmentation fault',
        r'core dumped',
        r'timeout',
        r'out of memory',
        r'compilation error',
        r'test.*failed',
        r'assertion.*failed'
    ]
    
    # Warning patterns
    WARNING_PATTERNS = [
        r'warning:',
        r'deprecated',
        r'caution',
        r'attention'
    ]
    
    def __init__(self):
        self.error_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.ERROR_PATTERNS]
        self.warning_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.WARNING_PATTERNS]
    
    def extract_features(self, log_content: str) -> Dict[str, Any]:
        """Extract features from log content"""
        if not log_content:
            return self._empty_features()
        
        lines = log_content.split('\n')
        
        features = {
            'total_lines': len(lines),
            'error_count': self._count_patterns(lines, self.error_regex),
            'warning_count': self._count_patterns(lines, self.warning_regex),
            'unique_errors': self._extract_unique_errors(lines),
            'error_types': self._classify_errors(lines),
            'log_length': len(log_content),
            'has_timeout': self._check_timeout(log_content),
            'has_oom': self._check_oom(log_content),
            'test_failures': self._count_test_failures(lines),
            'compilation_errors': self._count_compilation_errors(lines)
        }
        
        return features
    
    def _count_patterns(self, lines: List[str], patterns: List[re.Pattern]) -> int:
        """Count occurrences of regex patterns"""
        count = 0
        for line in lines:
            for pattern in patterns:
                if pattern.search(line):
                    count += 1
                    break
        return count
    
    def _extract_unique_errors(self, lines: List[str]) -> List[str]:
        """Extract unique error messages"""
        errors = set()
        for line in lines:
            for pattern in self.error_regex:
                if pattern.search(line):
                    # Extract the error line (simplified)
                    cleaned = line.strip()[:200]  # First 200 chars
                    errors.add(cleaned)
        return list(errors)[:10]  # Return top 10
    
    def _classify_errors(self, lines: List[str]) -> Dict[str, int]:
        """Classify error types"""
        error_types = {
            'compilation': 0,
            'runtime': 0,
            'test': 0,
            'timeout': 0,
            'memory': 0,
            'network': 0,
            'other': 0
        }
        
        compilation_keywords = ['compile', 'syntax', 'parse']
        runtime_keywords = ['exception', 'traceback', 'segfault']
        test_keywords = ['test', 'assert', 'expect']
        timeout_keywords = ['timeout', 'timed out']
        memory_keywords = ['out of memory', 'oom', 'memory']
        network_keywords = ['connection', 'network', 'unreachable']
        
        for line in lines:
            line_lower = line.lower()
            
            if any(kw in line_lower for kw in compilation_keywords):
                error_types['compilation'] += 1
            elif any(kw in line_lower for kw in runtime_keywords):
                error_types['runtime'] += 1
            elif any(kw in line_lower for kw in test_keywords):
                error_types['test'] += 1
            elif any(kw in line_lower for kw in timeout_keywords):
                error_types['timeout'] += 1
            elif any(kw in line_lower for kw in memory_keywords):
                error_types['memory'] += 1
            elif any(kw in line_lower for kw in network_keywords):
                error_types['network'] += 1
            elif any(pattern.search(line) for pattern in self.error_regex):
                error_types['other'] += 1
        
        return error_types
    
    def _check_timeout(self, log_content: str) -> bool:
        """Check if log contains timeout errors"""
        timeout_pattern = re.compile(r'timeout|timed out', re.IGNORECASE)
        return bool(timeout_pattern.search(log_content))
    
    def _check_oom(self, log_content: str) -> bool:
        """Check if log contains out-of-memory errors"""
        oom_pattern = re.compile(r'out of memory|oom killed', re.IGNORECASE)
        return bool(oom_pattern.search(log_content))
    
    def _count_test_failures(self, lines: List[str]) -> int:
        """Count test failures"""
        test_fail_pattern = re.compile(r'test.*failed|failed.*test|\d+\s+failed', re.IGNORECASE)
        count = 0
        for line in lines:
            if test_fail_pattern.search(line):
                count += 1
        return count
    
    def _count_compilation_errors(self, lines: List[str]) -> int:
        """Count compilation errors"""
        compile_error_pattern = re.compile(r'compilation error|compile.*failed', re.IGNORECASE)
        count = 0
        for line in lines:
            if compile_error_pattern.search(line):
                count += 1
        return count
    
    def _empty_features(self) -> Dict[str, Any]:
        """Return empty feature set"""
        return {
            'total_lines': 0,
            'error_count': 0,
            'warning_count': 0,
            'unique_errors': [],
            'error_types': {
                'compilation': 0,
                'runtime': 0,
                'test': 0,
                'timeout': 0,
                'memory': 0,
                'network': 0,
                'other': 0
            },
            'log_length': 0,
            'has_timeout': False,
            'has_oom': False,
            'test_failures': 0,
            'compilation_errors': 0
        }
    
    def summarize_logs(self, log_content: str, max_lines: int = 50) -> str:
        """Create a summary of log content"""
        if not log_content:
            return "No log content available"
        
        lines = log_content.split('\n')
        
        # Extract error lines
        error_lines = []
        for line in lines:
            if any(pattern.search(line) for pattern in self.error_regex):
                error_lines.append(line.strip())
        
        if error_lines:
            summary = "Key Errors:\n" + "\n".join(error_lines[:max_lines])
        else:
            # Return last N lines if no errors
            summary = "Last lines:\n" + "\n".join(lines[-max_lines:])
        
        return summary


# Singleton instance
log_processor = LogProcessor()
