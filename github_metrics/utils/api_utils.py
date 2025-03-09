import os
import requests

def validate_github_token(token_file, logger):
    """
    Validate GitHub token and prepare API headers.
    
    Args:
        token_file (str): Path to the file containing GitHub token
        logger (logging.Logger): Logger instance
        
    Returns:
        dict: API headers with token or None if validation fails
    """
    try:
        logger.info("Validating GitHub authentication...")
        
        # Get token from file or environment
        token = get_github_token(token_file, logger)
            
        if not token:
            logger.error("No GitHub token found - authentication will fail")
            return None
            
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Verify token works
        response = requests.get(
            'https://api.github.com/user',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("GitHub authentication successful")
            
            # Check rate limits
            rate_response = requests.get(
                'https://api.github.com/rate_limit',
                headers=headers
            )
            
            if rate_response.status_code == 200:
                limits = rate_response.json()['rate']
                logger.info(f"API Rate Limits: {limits['remaining']}/{limits['limit']} remaining")
            
            return headers
        
        logger.error(f"Authentication failed with status {response.status_code}")
        return None
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return None

def get_github_token(token_file, logger):
    """
    Get GitHub token with flexible sourcing options.
    Prioritizes token file, then environment variables.
    
    Args:
        token_file (str): Path to token file
        logger (logging.Logger): Logger instance
        
    Returns:
        str: GitHub token or None if not found
    """
    token = None
    
    # Try to read from token file first
    if token_file and os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                token = f.read().strip()
            logger.info("Using GitHub token from file")
            return token
        except Exception as e:
            logger.warning(f"Error reading token file: {str(e)}")
    
    # Check for GitHub token environment variable
    token = os.getenv('GITHUB_TOKEN')
    if token:
        logger.info("Using GitHub token from environment variable")
        return token
    
    return None