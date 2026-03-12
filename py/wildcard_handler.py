import logging
import random
import re
import time
import hashlib
import datetime
from typing import Any
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

def get_random_line_from_wildcard(wildcard_name: str, base_dir: str | None = None, force_refresh: str | None = None) -> str:
    """
    Get a random line from a wildcard file.
    
    Args:
        wildcard_name (str): Name of the wildcard without .txt extension
        base_dir (str, optional): Base directory for wildcards. Defaults to the root wildcards directory.
        force_refresh (str, optional): Force refresh string to add randomness to selection
        
    Returns:
        str: A randomly selected line from the wildcard file, or the original wildcard token if error
    """
    lines: list[str] | None = None
    entropy_string: str | None = None
    entropy_hash: str | None = None
    wildcard_path: Path | None = None
    
    try:
        # Default to the root wildcards directory if no base_dir provided
        if not base_dir:
            base_dir_path: Path = Path("/AI/wildcards")  # Default wildcards directory
        else:
            base_dir_path = Path(base_dir)
        
        # DEBUG: Log what we received and resolved
        logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} base_dir param: {base_dir}")
        logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} resolved base_dir_path: {base_dir_path}")
        
        # Ensure wildcard_name is clean and has .txt extension
        wildcard_name = wildcard_name.strip()
        logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} wildcard_name (stripped): {wildcard_name}")
        
        if not wildcard_name.endswith('.txt'):
            wildcard_name = f"{wildcard_name}.txt"
        
        logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} wildcard_name (with .txt): {wildcard_name}")
        
        wildcard_path = base_dir_path / wildcard_name
        logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} final wildcard_path: {wildcard_path}")
        
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
            # Create entropy using force_refresh value and wildcard name
            # Don't call time.time() again - use the passed force_refresh value
            entropy_string = f"{force_refresh}{wildcard_name}{len(lines)}{datetime.datetime.now().microsecond}"
            entropy_hash = hashlib.md5(entropy_string.encode()).hexdigest()
            
            # Create a new Random instance to avoid affecting global state
            rng = random.Random(hash(entropy_hash))
            random_index = rng.randint(0, len(lines) - 1)
            
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

def get_unique_replacement_from_wildcard(wildcard_name: str, base_dir: str | None = None, force_refresh: str | None = None, used_replacements: set[str] | None = None, max_attempts: int = 50) -> str:
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
    lines: list[str] | None = None
    available_lines: list[str] | None = None
    entropy_string: str | None = None
    entropy_hash: str | None = None
    wildcard_path: Path | None = None
    
    try:
        if used_replacements is None:
            used_replacements = set()
        
        # Default to the root wildcards directory if no base_dir provided
        if not base_dir:
            base_dir_path: Path = Path("/AI/wildcards")  # Default wildcards directory
        else:
            base_dir_path = Path(base_dir)
        
        # DEBUG: Log what we received and resolved
        logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} [get_unique] base_dir param: {base_dir}")
        logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} [get_unique] resolved base_dir_path: {base_dir_path}")
        
        # Ensure wildcard_name is clean and has .txt extension
        wildcard_name = wildcard_name.strip()
        logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} [get_unique] wildcard_name (stripped): {wildcard_name}")
        
        if not wildcard_name.endswith('.txt'):
            wildcard_name = f"{wildcard_name}.txt"
        
        logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} [get_unique] wildcard_name (with .txt): {wildcard_name}")
        
        wildcard_path = base_dir_path / wildcard_name
        logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} [get_unique] final wildcard_path: {wildcard_path}")
        
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
                # Create entropy using force_refresh value, wildcard name, and attempt
                # Don't call time.time() again - use the passed force_refresh value
                entropy_string = f"{force_refresh}{wildcard_name}{len(available_lines)}{attempt}{datetime.datetime.now().microsecond}"
                entropy_hash = hashlib.md5(entropy_string.encode()).hexdigest()
                
                # Create a new Random instance to avoid affecting global state
                rng = random.Random(hash(entropy_hash))
                random_index = rng.randint(0, len(available_lines) - 1)
                
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

def process_wildcards_in_text(text: str, base_dir: str | None = None, force_refresh: str | None = None, max_depth: int = 10) -> str:
    """
    Process all wildcard tokens in a text string, including nested wildcards.
    
    Args:
        text (str): The text containing wildcard tokens (__token__)
        base_dir (str, optional): Base directory for wildcards
        force_refresh (str, optional): Force refresh string to add randomness to selection
        max_depth (int): Maximum recursion depth for nested wildcards (default: 10)
        
    Returns:
        str: Text with wildcard tokens replaced by random lines, including nested wildcards
    """
    matches: list[Any] | None = None
    used_replacements: set[str] | None = None
    
    # DEBUG: Log what we received
    logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} [process_wildcards_in_text] Called with base_dir: {base_dir}")
    logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} [process_wildcards_in_text] force_refresh: {force_refresh}")
    logger.debug(f"{Colors.BLUE}[BASIFY Wildcards DEBUG]{Colors.ENDC} [process_wildcards_in_text] text length: {len(text) if text else 0}")
    
    try:
        if not text:
            return text
        
        # Track processed states to detect infinite loops
        processed_text = text
        current_depth = 0
        
        # Continue processing until no wildcards remain or max depth is reached
        while current_depth < max_depth:
            # Find all wildcard tokens using pre-compiled pattern
            matches = list(WILDCARD_PATTERN.finditer(processed_text))
            
            if not matches:
                # No more wildcards to process
                if current_depth > 0:
                    logger.info(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.GREEN}Completed nested wildcard processing at depth {current_depth}{Colors.ENDC}")
                return processed_text
            
            if current_depth == 0:
                logger.info(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.GREEN}Found {len(matches)} wildcard token occurrences to process{Colors.ENDC}")
            else:
                logger.info(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.GREEN}Found {len(matches)} nested wildcard token occurrences at depth {current_depth}{Colors.ENDC}")
            
            # Track used replacements to avoid duplicates within this iteration
            used_replacements = set()
            
            # Store text before processing to detect if anything changed
            text_before_processing = processed_text
            
            # Process each token occurrence individually for unique replacements
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
            
            # Check if text actually changed after processing
            if processed_text == text_before_processing:
                # No changes were made - this means all wildcards returned their original tokens
                # This could indicate missing files or circular references
                logger.warning(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.YELLOW}No changes made during wildcard processing at depth {current_depth} - wildcards may reference missing files or create circular references{Colors.ENDC}")
                return processed_text
            
            # Clear used_replacements for next iteration
            used_replacements.clear()
            current_depth += 1
        
        # If we exit the loop due to max_depth, log a warning
        if current_depth >= max_depth and WILDCARD_PATTERN.search(processed_text):
            logger.warning(f"{Colors.BLUE}[BASIFY Wildcards]{Colors.ENDC} {Colors.YELLOW}Maximum wildcard nesting depth ({max_depth}) reached, some wildcards may remain unprocessed{Colors.ENDC}")
        
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
