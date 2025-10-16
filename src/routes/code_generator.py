"""
Main code generation and deployment routes.
"""

import logging
import time
import os
import threading
from flask import Blueprint, request, jsonify
from typing import Dict, Any

from src.services.gemini_service import GeminiCodeGenerator
from src.services.github_service import GitHubService
from src.services.evaluation_service import EvaluationService
from src.utils.file_generator import FileGenerator
from src.middleware.validation import validate_request, TaskBasedRequestSchema, LegacyCodeGenerationRequestSchema

# Create blueprint
code_generator_bp = Blueprint('code_generator', __name__)

def _process_task_in_background(data: Dict[str, Any]):
    """
    Background task to process code generation and deployment.
    This runs in a separate thread after the API responds.
    """
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    try:
        # Extract task data
        task_id = data['task']
        round_num = data['round']
        brief = data['brief']
        checks = data['checks']
        evaluation_url = data['evaluation_url']
        nonce = data['nonce']
        email = data['email']
        
        logger.info(f"Background processing started for task: {task_id} (Round {round_num})")
        
        # Initialize services
        evaluation_service = EvaluationService()
        
        # Generate repository name
        repo_name = evaluation_service.generate_repository_name(task_id, round_num)
        logger.info(f"Background Step 0: repo name {repo_name}")
        
        # Step 1: Generate code using Gemini
        logger.info("Background Step 1: Generating code with Gemini AI for task")
        gemini_service = GeminiCodeGenerator()
        generation_result = gemini_service.generate_code_from_task(data)
        
        generated_files = generation_result['files']
        logger.info(f"Generated {len(generated_files)} files")
        
        # Step 2: Generate additional project files
        logger.info("Background Step 2: Generating project files (README, LICENSE, tests, workflow)")
        
        # Convert checks to tests for compatibility
        test_cases = evaluation_service.convert_checks_to_tests(checks)
        
        # Generate README
        readme_content = FileGenerator.generate_readme(
            repo_name=repo_name,
            description=f"Task: {task_id} - {brief}",
            language='javascript',
            tests=test_cases
        )
        
        # Generate LICENSE (always MIT as per common check requirement)
        license_content = FileGenerator.generate_license(
            license_type='mit',
            author=f"AI Generated Project for {email}"
        )
        
        # Generate GitHub Actions workflow
        workflow_content = FileGenerator.generate_github_workflow(
            language='javascript',
            repo_name=repo_name
        )
        
        # Generate test files
        test_files = FileGenerator.generate_test_files(test_cases, 'javascript')
        
        # Combine all files
        all_files = {
            'README.md': readme_content,
            'LICENSE': license_content,
            '.github/workflows/ci.yml': workflow_content,
            **generated_files,
            **test_files
        }
        
        logger.info(f"Total files to commit: {len(all_files)}")
        logger.info(f"********Ending***************")
        
        # Step 3: Create GitHub repository
        logger.info("Background Step 3: Creating GitHub repository")
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            logger.error("GitHub token not configured")
            return
        
        github_service = GitHubService(github_token)
        
        repo_info = github_service.create_repository(
            repo_name=repo_name,
            description=f"AI-generated solution for task {task_id} (Round {round_num}): {brief[:100]}...",
            private=False
        )
        
        logger.info(f"Repository created: {repo_info['html_url']}")
        
        # Step 4: Push files to repository
        logger.info("Background Step 4: Pushing files to repository")
        commit_result = github_service.add_files_to_repository(
            repo_name=repo_name,
            files=all_files,
            commit_message=f"Initial commit - AI generated solution for task {task_id} round {round_num}"
        )
        
        # Extract commit SHA
        commit_sha = commit_result.get('commit', {}).get('sha', 'unknown') if commit_result else 'unknown'
        logger.info(f"Files committed with SHA: {commit_sha}")
        
        # Step 5: Enable GitHub Pages
        logger.info("Background Step 5: Enabling GitHub Pages")
#        try:
#            pages_info = github_service.enable_github_pages(
#                repo_name=repo_name,
#                source_branch='main',
#                source_path='/'
#            )
#            pages_url = pages_info.get('url', '')
#            pages_status = pages_info.get('status', 'unknown')
#        except Exception as e:
#            logger.warning(f"Failed to enable GitHub Pages: {str(e)}")
#            pages_url = f"https://{github_service.username}.github.io/{repo_name}"
#            pages_status = "manual_setup_required"
        
        # Step 6: Send evaluation callback
        logger.info("Background Step 6: Sending evaluation callback")
        repo_info['pages_url'] = None
        #pages_url
        callback_success = evaluation_service.send_evaluation_callback(
            evaluation_url=evaluation_url,
            repo_info=repo_info,
            task_data=data,
            commit_sha=commit_sha
        )
        
        execution_time = time.time() - start_time
        
        if callback_success:
            logger.info(f"Task {task_id} completed successfully in {execution_time:.2f} seconds")
        else:
            logger.warning(f"Task {task_id} completed but callback failed in {execution_time:.2f} seconds")
            
    except Exception as e:
        logger.error(f"Background processing failed for task {data.get('task', 'unknown')}: {str(e)}")
        
        # Try to send error callback
        try:
            evaluation_service = EvaluationService()
            evaluation_service.send_evaluation_callback(
                evaluation_url=data.get('evaluation_url', ''),
                repo_info={},
                task_data=data,
                error=str(e)
            )
        except:
            logger.error("Failed to send error callback")

@code_generator_bp.route('/generate-and-deploy-task', methods=['POST'])
@validate_request(TaskBasedRequestSchema)
def generate_and_deploy_task(data: Dict[str, Any]):
    """
    Task-based endpoint that validates request and starts background processing.
    Returns immediately with 200 after validation.
    
    Expected payload:
    {
        "email": "user@example.com",
        "secret": "secure-secret",
        "task": "captcha-solver-v1",
        "round": 1,
        "nonce": "abc123",
        "brief": "Create a captcha solver...",
        "checks": ["Repo has MIT license", "README.md is professional", ...],
        "evaluation_url": "https://example.com/notify",
        "attachments": [{"name": "sample.png", "url": "data:image/png;base64,..."}]
    }
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Step 1: Validate secret
        evaluation_service = EvaluationService()
        if not evaluation_service.validate_secret(data['secret']):
            return jsonify({
                'success': False,
                'error': 'Invalid secret',
                'message': 'Authentication failed'
            }), 401
        
        # Step 2: Extract and validate basic task data
        task_id = data['task']
        round_num = data['round']
        nonce = data['nonce']
        email = data['email']
        evaluation_url = data['evaluation_url']
        
        logger.info(f"Task accepted for background processing: {task_id} (Round {round_num})")
        
        # Step 3: Start background processing
        background_thread = threading.Thread(
            target=_process_task_in_background,
            args=(data,),
            daemon=True  # Thread will die when main process dies
        )
        background_thread.start()
        
        # Step 4: Return immediate response
        response = {
            'success': True,
            'message': 'Task accepted and is being processed in the background',
            'task': {
                'id': task_id,
                'round': round_num,
                'nonce': nonce,
                'email': email,
                'status': 'processing'
            },
            'evaluation_url': evaluation_url,
            'note': 'A callback will be sent to the evaluation_url when processing completes'
        }
        
        logger.info(f"Task {task_id} accepted and background processing started")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in generate_and_deploy_task: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to accept task for processing'
        }), 500

@code_generator_bp.route('/generate-and-deploy', methods=['POST'])
@validate_request(LegacyCodeGenerationRequestSchema)
def generate_and_deploy(data: Dict[str, Any]):
    """
    Main endpoint that generates code, creates GitHub repository, and deploys.
    
    Expected payload:
    {
        "instructions": "Create a simple calculator...",
        "tests": [{"description": "...", "input": "...", "expected_output": "..."}],
        "repository_name": "my-calculator",
        "license": "mit",
        "github_token": "ghp_...",
        "language": "javascript",
        "framework": "vanilla"
    }
    """
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    try:
        # Extract data from validated request
        instructions = data['instructions']
        tests = data['tests']
        repo_name = data['repository_name']
        license_type = data.get('license', 'mit')
        github_token = data['github_token']
        language = data.get('language', 'javascript')
        framework = data.get('framework', 'vanilla')
        
        logger.info(f"Starting code generation and deployment for: {repo_name}")
        
        # Step 1: Generate code using Gemini
        logger.info("Step 1: Generating code with Gemini AI")
        gemini_service = GeminiCodeGenerator()
        generation_result = gemini_service.generate_code(
            instructions=instructions,
            language=language,
            framework=framework,
            tests=tests
        )
        
        generated_files = generation_result['files']
        logger.info(f"Generated {len(generated_files)} files")
        
        # Step 2: Generate additional project files
        logger.info("Step 2: Generating project files (README, LICENSE, tests, workflow)")
        
        # Generate README
        readme_content = FileGenerator.generate_readme(
            repo_name=repo_name,
            description=instructions,
            language=language,
            tests=tests
        )
        
        # Generate LICENSE
        license_content = FileGenerator.generate_license(
            license_type=license_type,
            author="AI Generated Project"
        )
        
        # Generate GitHub Actions workflow
        workflow_content = FileGenerator.generate_github_workflow(
            language=language,
            repo_name=repo_name
        )
        
        # Generate test files
        test_files = FileGenerator.generate_test_files(tests, language)
        
        # Combine all files
        all_files = {
            'README.md': readme_content,
            'LICENSE': license_content,
            '.github/workflows/ci.yml': workflow_content,
            **generated_files,
            **test_files
        }
        
        logger.info(f"Total files to commit: {len(all_files)}")
        
        # Step 3: Create GitHub repository
        logger.info("Step 3: Creating GitHub repository")
        github_service = GitHubService(github_token)
        
        repo_info = github_service.create_repository(
            repo_name=repo_name,
            description=f"AI-generated {language} application: {instructions[:100]}...",
            private=False
        )
        
        logger.info(f"Repository created: {repo_info['html_url']}")
        
        # Step 4: Push files to repository
        logger.info("Step 4: Pushing files to repository")
        github_service.add_files_to_repository(
            repo_name=repo_name,
            files=all_files,
            commit_message="Initial commit - AI generated code with tests and CI/CD"
        )
        
        # Step 5: Enable GitHub Pages (all apps are static now)
        logger.info("Step 5: Enabling GitHub Pages")
        try:
            pages_info = github_service.enable_github_pages(
                repo_name=repo_name,
                source_branch='main',
                source_path='/'
            )
            pages_url = pages_info.get('url', '')
            pages_status = pages_info.get('status', 'unknown')
        except Exception as e:
            logger.warning(f"Failed to enable GitHub Pages: {str(e)}")
            pages_url = f"https://{github_service.username}.github.io/{repo_name}"
            pages_status = "manual_setup_required"
        
        # Step 6: Get initial workflow status
        logger.info("Step 6: Checking initial workflow status")
        workflow_runs = github_service.get_workflow_runs(repo_name)
        
        execution_time = time.time() - start_time
        
        # Prepare response for static web application
        response = {
            'success': True,
            'repository': {
                'name': repo_info['name'],
                'full_name': repo_info['full_name'],
                'html_url': repo_info['html_url'],
                'clone_url': repo_info['clone_url']
            },
            'deployment': {
                'type': 'static_site',
                'pages_url': pages_url,
                'pages_status': pages_status,
                'workflow_runs': workflow_runs,
                'note': 'Static web application deployed to GitHub Pages'
            },
            'generated_files': list(all_files.keys()),
            'metadata': {
                'language': language,
                'framework': framework,
                'tests_count': len(tests),
                'files_count': len(all_files),
                'execution_time_seconds': round(execution_time, 2),
                'deployment_type': 'github_pages'
            },
            'message': f"Successfully created and deployed {repo_name} to GitHub Pages!"
        }
        
        logger.info(f"Completed in {execution_time:.2f} seconds")
        return jsonify(response), 201
        
    except Exception as e:
        logger.error(f"Error in generate_and_deploy: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate and deploy code'
        }), 500

@code_generator_bp.route('/status/<repo_name>', methods=['GET'])
def get_deployment_status(repo_name: str):
    """
    Check the deployment status of a repository.
    Requires GitHub token in Authorization header.
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Get GitHub token from header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'GitHub token required in Authorization header'}), 401
        
        github_token = auth_header.replace('Bearer ', '')
        github_service = GitHubService(github_token)
        
        # Get workflow runs
        workflow_runs = github_service.get_workflow_runs(repo_name)
        
        # Try to get pages info
        try:
            pages_info = github_service.enable_github_pages(repo_name)
            pages_url = pages_info.get('url', '')
            pages_status = pages_info.get('status', 'unknown')
        except:
            pages_url = f"https://{github_service.username}.github.io/{repo_name}"
            pages_status = "unknown"
        
        return jsonify({
            'success': True,
            'repository_name': repo_name,
            'deployment': {
                'pages_url': pages_url,
                'pages_status': pages_status,
                'workflow_runs': workflow_runs
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting deployment status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to get deployment status'
        }), 500

@code_generator_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the code generator service."""
    return jsonify({
        'status': 'healthy',
        'service': 'code-generator',
        'endpoints': [
            '/api/generate-and-deploy-task',
            '/api/generate-and-deploy',
            '/api/status/<repo_name>',
            '/api/health'
        ]
    }), 200