import logging
import random
import os
import re
import time
import hashlib
import datetime
from pathlib import Path

class Colors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    ENDC   = '\033[0m'  # Resets the color

logger = logging.getLogger(__name__)

# Compile regex pattern once at module level for efficiency
WILDCARD_PATTERN = re.compile(r'__(.+?)__')

def get_random_line_from_wildcard(wildcard_name, base_dir=None, force_refresh=None):
    """
    Get a random line from a wildcard file.
    
    Args:
        wildcard_name (str): Name of the wildcard without .txt extension
        base_dir (str, optional): Base directory for wildcards. Defaults to the root wildcards directory.
        force_refresh (str, optional): Force refresh string to add randomness to selection
        
    Returns:
        str: A randomly selected line from the wildcard file, or the original wildcard token if error
    """
    lines = None
    entropy_string = None
    entropy_hash = None
    
    try:
        # Default to the root wildcards directory if no base_dir provided
        if not base_dir:
            comfyui_root = Path(__file__).parent.parent.parent.parent  # Go up to ComfyUI root
            base_dir = comfyui_root / "wildcards"  # Default wildcards directory
        else:
            base_dir = Path(base_dir)
        
        # Ensure wildcard_name is clean and has .txt extension
        wildcard_name = wildcard_name.strip()
        if not wildcard_name.endswith('.txt'):
            wildcard_name = f"{wildcard_name}.txt"
        
        wildcard_path = base_dir / wildcard_name
        
        # Check if file exists
        if not wildcard_path.exists():
            logger.warning(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.YELLOW}Wildcard file not found: {wildcard_path}{Colors.ENDC}")
            return f"__{wildcard_name.replace('.txt', '')}__"
        
        # Read file content
        with open(wildcard_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
        if not lines:
            logger.warning(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.YELLOW}No valid lines in wildcard file: {wildcard_path}{Colors.ENDC}")
            return f"__{wildcard_name.replace('.txt', '')}__"
        
        # Select random line with enhanced randomness
        if force_refresh:
            # Create a more random seed using current time, force_refresh string, and wildcard name
            entropy_string = f"{time.time()}{force_refresh}{wildcard_name}{len(lines)}"
            entropy_hash = hashlib.md5(entropy_string.encode()).hexdigest()
            
            # Use multiple random selections to increase randomness
            random.seed(hash(entropy_hash))
            random_index = random.randint(0, len(lines) - 1)
            
            # Additional randomization: use current microsecond as secondary selection
            microsecond_seed = datetime.datetime.now().microsecond
            random.seed(microsecond_seed + hash(force_refresh))
            random_index = (random_index + random.randint(0, len(lines) - 1)) % len(lines)
            
            random_line = lines[random_index]
            
            # Don't delete here - let finally block handle cleanup
        else:
            # Standard random selection
            random_line = random.choice(lines)
        
        # Don't delete here - let finally block handle cleanup
            
        logger.info(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.GREEN}Selected from {wildcard_name}: {random_line[:30]}...{Colors.ENDC}" if len(random_line) > 30 else f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.GREEN}Selected from {wildcard_name}: {random_line}{Colors.ENDC}")
        
        return random_line
        
    except Exception as e:
        logger.error(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.RED}Error processing wildcard file {wildcard_path}: {str(e)}{Colors.ENDC}")
        return f"__{wildcard_name.replace('.txt', '')}__"
    finally:
        # Ensure cleanup even on error - use try/except since del removes from namespace
        try:
            del lines
        except (NameError, UnboundLocalError):
            pass
        try:
            del entropy_string
        except (NameError, UnboundLocalError):
            pass
        try:
            del entropy_hash
        except (NameError, UnboundLocalError):
            pass

def get_unique_replacement_from_wildcard(wildcard_name, base_dir=None, force_refresh=None, used_replacements=None, max_attempts=50):
    """
    Get a unique random line from a wildcard file that hasn't been used yet.
    
    Args:
        wildcard_name (str): Name of the wildcard without .txt extension
        base_dir (str, optional): Base directory for wildcards
        force_refresh (str, optional): Force refresh string to add randomness to selection
        used_replacements (set, optional): Set of already used replacements to avoid
        max_attempts (int): Maximum attempts to find a unique replacement
        
    Returns:
        str: A randomly selected line that hasn't been used yet, or fallback to any line if all are used
    """
    lines = None
    available_lines = None
    entropy_string = None
    entropy_hash = None
    
    try:
        if used_replacements is None:
            used_replacements = set()
        
        # Default to the root wildcards directory if no base_dir provided
        if not base_dir:
            comfyui_root = Path(__file__).parent.parent.parent.parent  # Go up to ComfyUI root
            base_dir = comfyui_root / "wildcards"  # Default wildcards directory
        else:
            base_dir = Path(base_dir)
        
        # Ensure wildcard_name is clean and has .txt extension
        wildcard_name = wildcard_name.strip()
        if not wildcard_name.endswith('.txt'):
            wildcard_name = f"{wildcard_name}.txt"
        
        wildcard_path = base_dir / wildcard_name
        
        # Check if file exists
        if not wildcard_path.exists():
            logger.warning(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.YELLOW}Wildcard file not found: {wildcard_path}{Colors.ENDC}")
            return f"__{wildcard_name.replace('.txt', '')}__"
        
        # Read file content
        with open(wildcard_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
        if not lines:
            logger.warning(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.YELLOW}No valid lines in wildcard file: {wildcard_path}{Colors.ENDC}")
            return f"__{wildcard_name.replace('.txt', '')}__"
        
        # If we've used all available lines, reset and allow duplicates
        available_lines = [line for line in lines if line not in used_replacements]
        if not available_lines:
            logger.info(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.YELLOW}All lines from {wildcard_name} have been used, allowing duplicates{Colors.ENDC}")
            available_lines = lines
        
        # Try to get a unique replacement
        for attempt in range(max_attempts):
            # Select random line with enhanced randomness
            if force_refresh:
                # Create a more random seed using current time, force_refresh string, wildcard name, and attempt
                entropy_string = f"{time.time()}{force_refresh}{wildcard_name}{len(available_lines)}{attempt}"
                entropy_hash = hashlib.md5(entropy_string.encode()).hexdigest()
                
                # Use multiple random selections to increase randomness
                random.seed(hash(entropy_hash))
                random_index = random.randint(0, len(available_lines) - 1)
                
                # Additional randomization: use current microsecond as secondary selection
                microsecond_seed = datetime.datetime.now().microsecond
                random.seed(microsecond_seed + hash(force_refresh) + attempt)
                random_index = (random_index + random.randint(0, len(available_lines) - 1)) % len(available_lines)
                
                random_line = available_lines[random_index]
                
                # Don't delete in loop - let finally block handle cleanup
            else:
                # Standard random selection
                random_line = random.choice(available_lines)
            
            # If this line hasn't been used, return it
            if random_line not in used_replacements:
                logger.info(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.GREEN}Selected unique line from {wildcard_name}: {random_line[:30]}...{Colors.ENDC}" if len(random_line) > 30 else f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.GREEN}Selected unique line from {wildcard_name}: {random_line}{Colors.ENDC}")
                
                # Don't delete here - let finally block handle cleanup
                
                return random_line
        
        # If we couldn't find a unique line after max_attempts, just return a random one
        logger.warning(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.YELLOW}Could not find unique replacement after {max_attempts} attempts, returning duplicate{Colors.ENDC}")
        result = random.choice(lines)
        
        # Don't delete here - let finally block handle cleanup
        
        return result
        
    except Exception as e:
        logger.error(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.RED}Error processing wildcard file {wildcard_path}: {str(e)}{Colors.ENDC}")
        return f"__{wildcard_name.replace('.txt', '')}__"
    finally:
        # Ensure cleanup even on error - use try/except since del removes from namespace
        try:
            del lines
        except (NameError, UnboundLocalError):
            pass
        try:
            del available_lines
        except (NameError, UnboundLocalError):
            pass
        try:
            del entropy_string
        except (NameError, UnboundLocalError):
            pass
        try:
            del entropy_hash
        except (NameError, UnboundLocalError):
            pass

def process_wildcards_in_text(text, base_dir=None, force_refresh=None):
    """
    Process all wildcard tokens in a text string.
    
    Args:
        text (str): The text containing wildcard tokens (__token__)
        base_dir (str, optional): Base directory for wildcards
        force_refresh (str, optional): Force refresh string to add randomness to selection
        
    Returns:
        str: Text with wildcard tokens replaced by random lines
    """
    matches = None
    used_replacements = None
    
    try:
        if not text:
            return text
        
        # Find all wildcard tokens using pre-compiled pattern
        matches = list(WILDCARD_PATTERN.finditer(text))
        
        if not matches:
            return text
        
        logger.info(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.GREEN}Found {len(matches)} wildcard token occurrences to process{Colors.ENDC}")
        
        # Track used replacements to avoid duplicates
        used_replacements = set()
        
        # Process each token occurrence individually for unique replacements
        processed_text = text
        
        # Process from the end to avoid position shifts during replacement
        for match in reversed(matches):
            token = match.group(1)
            start_pos = match.start()
            end_pos = match.end()
            
            # Get unique replacement for each individual occurrence
            replacement = get_unique_replacement_from_wildcard(token, base_dir, force_refresh, used_replacements)
            used_replacements.add(replacement)
            
            # Replace this specific occurrence
            processed_text = processed_text[:start_pos] + replacement + processed_text[end_pos:]
        
        # Don't delete here - let finally block handle cleanup
        
        return processed_text
    finally:
        # Ensure cleanup even on error - use try/except since del removes from namespace
        try:
            del matches
        except (NameError, UnboundLocalError):
            pass
        try:
            del used_replacements
        except (NameError, UnboundLocalError):
            pass
