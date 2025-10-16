"""
Evaluation service for task management and callback handling.
"""

import logging
import requests
import os
from typing import Dict, Any, List

class EvaluationService:
    """Service for handling task evaluation and callbacks."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_secret(self, secret: str) -> bool:
        """
        Validate the provided secret against the API_SECRET environment variable.
        
        Args:
            secret: The secret to validate
            
        Returns:
            bool: True if secret is valid, False otherwise
        """
        api_secret = os.getenv('API_SECRET', "123456")
        if not api_secret:
            self.logger.warning("API_SECRET environment variable not set")
            return False
        
        return secret == api_secret
    
    def generate_repository_name(self, task_id: str, round_num: int) -> str:
        """
        Generate a repository name based on task ID and round number.
        
        Args:
            task_id: The task identifier
            round_num: The round number
            
        Returns:
            str: Generated repository name
        """
        # Clean task ID to be repo-name friendly
        clean_task_id = task_id.lower().replace('_', '-').replace(' ', '-')
        return f"{clean_task_id}-r{round_num}"
    
    def convert_checks_to_tests(self, checks: List[str]) -> List[Dict[str, Any]]:
        """
        Convert task checks to test case format for compatibility.
        
        Args:
            checks: List of check descriptions
            
        Returns:
            List of test case dictionaries
        """
        tests = []
        for i, check in enumerate(checks):
            tests.append({
                'description': check,
                'input': 'manual_verification',
                'expected_output': 'passes_check',
                'type': 'verification',
                'check_id': i + 1
            })
        return tests
    
    def send_evaluation_callback(self, evaluation_url: str, repo_info: Dict[str, Any], task_data: Dict[str, Any], commit_sha: str = None, error: str = None) -> bool:
        """
        Send evaluation callback to the provided URL.
        
        Args:
            evaluation_url: URL to send the callback to
            repo_info: Repository information
            task_data: Original task data
            commit_sha: The commit SHA from the repository creation
            error: Error message if task failed
            
        Returns:
            bool: True if callback was sent successfully, False otherwise
        """
        try:
            if error:
                # Send error callback
                callback_payload = {
                    "email": task_data['email'],
                    "task": task_data['task'],
                    "round": task_data['round'],
                    "nonce": task_data['nonce'],
                    "repo_url": "",
                    "commit_sha": "",
                    "pages_url": "",
                    "status": "failed",
                    "error": error
                }
            else:
                # Send success callback
                callback_payload = {
                    # Copy these from the request
                    "email": task_data['email'],
                    "task": task_data['task'],
                    "round": task_data['round'],
                    "nonce": task_data['nonce'],
                    # Send these based on GitHub repo and commit
                    "repo_url": repo_info['html_url'],
                    "commit_sha": commit_sha or "unknown",
                    "pages_url": repo_info.get('pages_url', ''),
                    "status": "completed"
                }
            
            response = requests.post(
                evaluation_url,
                json=callback_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                status = "error" if error else "success"
                self.logger.info(f"Evaluation {status} callback sent successfully to {evaluation_url}")
                return True
            else:
                self.logger.warning(f"Evaluation callback failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send evaluation callback: {str(e)}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'


