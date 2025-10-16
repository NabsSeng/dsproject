"""
GitHub API integration for repository creation and file management.
"""

import os
import logging
import base64
import requests
from typing import Dict, List, Any
from github import Github, GithubException

class GitHubService:
    """Service for GitHub repository operations."""
    
    def __init__(self, token: str):
        """Initialize GitHub service with token.""" 
        self.token = token
        self.github=Github(token)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"GitHubService initialized {self.token} ")        # Verify token
        print(f"GitHubService initialized {self.token}")
        try:
            user = self.github.get_user()
            self.username = user.login
            self.logger.info(f"Authenticated as GitHub user: {self.username}")
            print(f"Authenticated as GitHub user: {self.username}")

        except GithubException as e:
            raise ValueError(f"Invalid GitHub token: {str(e)}")
    
    def create_repository(self, repo_name: str, description: str = "", 
                         private: bool = False) -> Dict[str, str]:
        """
        Create a new GitHub repository.
        
        Args:
            repo_name: Name of the repository
            description: Repository description
            private: Whether the repository should be private
            
        Returns:
            Dictionary with repository information
        """
        try:
            self.logger.info(f"Creating repository: {repo_name}")
            
            # Create repository
            repo = self.github.get_user().create_repo(
                name=repo_name,
                description=description,
                private=private,
                auto_init=False,  # We'll add files manually
                has_issues=True,
                has_wiki=False,
                has_downloads=True
            )
            
            self.logger.info(f"Repository created successfully: {repo.html_url}")
            
            return {
                'name': repo.name,
                'full_name': repo.full_name,
                'html_url': repo.html_url,
                'clone_url': repo.clone_url,
                'ssh_url': repo.ssh_url,
                'default_branch': repo.default_branch or 'main'
            }
            
        except GithubException as e:
            self.logger.error(f"Failed to create repository: {str(e)}")
            raise Exception(f"Failed to create repository: {str(e)}")
    
    def add_files_to_repository(self, repo_name: str, files: Dict[str, str], 
                              commit_message: str = "Initial commit") -> bool:
        """
        Add multiple files to a repository in a single commit.
        
        Args:
            repo_name: Name of the repository
            files: Dictionary of filename -> content
            commit_message: Commit message
            
        Returns:
            True if successful
        """
        try:
            repo = self.github.get_user().get_repo(repo_name)
            print(f"Repository found: {repo.full_name}")
            
            # For empty repositories, use a different approach
            # First, try to get the default branch reference
            try:
                ref = repo.get_git_ref(f'heads/{repo.default_branch}')
                base_sha = ref.object.sha
                print(f"Found existing branch {repo.default_branch} with SHA: {base_sha}")
            except GithubException as e:
                print(f"No existing branch found: {e}")
                # Repository is completely empty, we'll create the first commit
                base_sha = None
            
            # If repository is empty, create files one by one using the Contents API
            if base_sha is None:
                print("Repository is empty, using Contents API approach")
                created_files = []
                
                for filename, content in files.items():
                    try:
                        print(f"Creating file {filename} with content length {len(content)}")
                        file_info = repo.create_file(
                            path=filename,
                            message=f"Add {filename}",
                            content=content,
                            branch='main'
                        )
                        created_files.append(filename)
                        print(f"Successfully created {filename}")
                    except GithubException as e:
                        print(f"Failed to create {filename}: {e}")
                        raise
                
                # Get the latest commit SHA after creating files
                ref = repo.get_git_ref('heads/main')
                final_commit_sha = ref.object.sha
                
                return {
                    'success': True,
                    'commit': {
                        'sha': final_commit_sha,
                        'message': commit_message,
                        'files_created': created_files
                    }
                }
            
            else:
                # Repository has existing commits, use Git API
                print("Repository has existing commits, using Git API")
                
                # Create blobs for each file
                blobs = {}
                for filename, content in files.items():
                    print(f"Creating blob for {filename} with content length {len(content)}")
                    blob = repo.create_git_blob(content, 'utf-8')
                    blobs[filename] = blob.sha
                    self.logger.info(f"Created blob for {filename} {blob.sha}")
                
                # Create tree
                tree_elements = []
                for filename, blob_sha in blobs.items():
                    tree_elements.append({
                        'path': filename,
                        'mode': '100644',  # Regular file
                        'type': 'blob',
                        'sha': blob_sha
                    })
                
                tree = repo.create_git_tree(tree_elements, base_sha)
                
                # Create commit
                parents = [repo.get_git_commit(base_sha)]
                commit = repo.create_git_commit(
                    message=commit_message,
                    tree=tree,
                    parents=parents
                )
                
                # Update reference
                repo.get_git_ref('heads/main').edit(commit.sha)
                
                self.logger.info(f"Successfully added {len(files)} files to {repo_name}")
                return {
                    'success': True,
                    'commit': {
                        'sha': commit.sha,
                        'message': commit_message,
                        'url': commit.html_url
                    }
                }
            
        except GithubException as e:
            self.logger.error(f"Failed to add files to repository: {str(e)}")
            raise Exception(f"Failed to add files to repository: {str(e)}")
    
    def enable_github_pages(self, repo_name: str, source_branch: str = 'main', 
                          source_path: str = '/') -> Dict[str, str]:
        """
        Enable GitHub Pages for a repository.
        
        Args:
            repo_name: Name of the repository
            source_branch: Branch to use for GitHub Pages
            source_path: Path in the branch to use (/ or /docs)
            
        Returns:
            Dictionary with GitHub Pages information
        """
        try:
            repo = self.github.get_user().get_repo(repo_name)
            print(f"Enabling GitHub Pages for {repo_name} at {source_branch}:{source_path}")

            # GitHub Pages API endpoint
            url = f"https://api.github.com/repos/{self.username}/{repo_name}/pages"
            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Explicitly configure to deploy from branch (not GitHub Actions)
            data = {
                'source': {
                    'branch': source_branch,
                    'path': source_path
                },
                'build_type': 'legacy'  # Ensures branch-based deployment, not GitHub Actions
            }
            print(f"Configuring GitHub Pages for {repo_name} - Branch: {source_branch}, Path: {source_path}, Build Type: legacy (branch-based)")
            
            response = requests.post(url, headers=headers, json=data)
            print(f"Pages creation response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                pages_info = response.json()
                print(f"Pages enabled successfully: {pages_info}")
                self.logger.info(f"GitHub Pages enabled for {repo_name} using branch deployment")
                return {
                    'url': pages_info.get('html_url', ''),
                    'status': pages_info.get('status', 'building'),
                    'source_branch': source_branch,
                    'source_path': source_path,
                    'build_type': pages_info.get('build_type', 'legacy')
                }
            elif response.status_code == 409:
                # Pages already enabled, get current status
                print("GitHub Pages already enabled, checking current configuration...")
                get_response = requests.get(url, headers=headers)
                
                if get_response.status_code == 200:
                    pages_info = get_response.json()
                    current_source = pages_info.get('source', {})
                    current_build_type = pages_info.get('build_type', 'legacy')
                    
                    print(f"Current Pages config: branch={current_source.get('branch')}, path={current_source.get('path')}, build_type={current_build_type}")
                    
                    # Return current configuration without modification
                    return {
                        'url': pages_info.get('html_url', ''),
                        'status': pages_info.get('status', 'built'),
                        'source_branch': current_source.get('branch', source_branch),
                        'source_path': current_source.get('path', source_path),
                        'build_type': current_build_type,
                        'already_enabled': True
                    }
            
            self.logger.error(f"Failed to enable GitHub Pages: {response.text}")
            raise Exception(f"Failed to enable GitHub Pages: {response.text}")
            
        except Exception as e:
            self.logger.error(f"Error enabling GitHub Pages: {str(e)}")
            raise Exception(f"Error enabling GitHub Pages: {str(e)}")
    
    def add_file_to_repository(self, repo_name: str, file_path: str, 
                             content: str, commit_message: str = "Add file") -> bool:
        """
        Add a single file to repository.
        
        Args:
            repo_name: Name of the repository
            file_path: Path of the file in the repository
            content: File content
            commit_message: Commit message
            
        Returns:
            True if successful
        """
        try:
            repo = self.github.get_user().get_repo(repo_name)
            
            # Check if file exists
            try:
                existing_file = repo.get_contents(file_path)
                # File exists, update it
                repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=content,
                    sha=existing_file.sha
                )
                self.logger.info(f"Updated file {file_path} in {repo_name}")
            except GithubException:
                # File doesn't exist, create it
                repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=content
                )
                self.logger.info(f"Created file {file_path} in {repo_name}")
            
            return True
            
        except GithubException as e:
            self.logger.error(f"Failed to add file to repository: {str(e)}")
            raise Exception(f"Failed to add file to repository: {str(e)}")
    
    def get_workflow_runs(self, repo_name: str) -> List[Dict]:
        """
        Get GitHub Actions workflow runs for a repository.
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            List of workflow run information
        """
        try:
            repo = self.github.get_user().get_repo(repo_name)
            runs = repo.get_workflow_runs()
            
            workflow_runs = []
            for run in runs[:5]:  # Get last 5 runs
                workflow_runs.append({
                    'id': run.id,
                    'status': run.status,
                    'conclusion': run.conclusion,
                    'workflow_id': run.workflow_id,
                    'created_at': run.created_at.isoformat(),
                    'html_url': run.html_url
                })
            
            return workflow_runs
            
        except GithubException as e:
            self.logger.error(f"Failed to get workflow runs: {str(e)}")
            return []
        
    def get_build_status(self, repo_name: str) -> List[Dict]:
        """
        Get GitHub Actions workflow runs for a repository.
        
        Args:
            repo_name: Name of the repository
        Returns:
            List of workflow run information
        """
        try:
            repo = self.github.get_user().get_repo(repo_name)
            runs = repo.get_workflow_runs() 
            
            workflow_runs = []
            for run in runs[:5]:  # Get last 5 runs
                workflow_runs.append({
                    'id': run.id,
                    'status': run.status,
                    'conclusion': run.conclusion,
                    'workflow_id': run.workflow_id,
                    'created_at': run.created_at.isoformat(),
                    'html_url': run.html_url
                })
            
            return workflow_runs
            
        except GithubException as e:
             self.logger.error(f"Failed to get workflow runs: {str(e)}")
             return []

    def push_core_api_to_repo(self, repo_name: str, description: str = "AI Code Generation API") -> Dict[str, str]:
        """
        Create a repository and push only the core API code (excluding UI app and callback dashboard).
        
        Args:
            repo_name: Name of the repository
            description: Repository description
            
        Returns:
            Dictionary with repository information
        """
        try:
            # Define the core API files to include
            core_files = {}
            base_path = "/home/ubuntu/cgen"
            
            # Main application files
            files_to_include = [
                "app.py",
                "requirements.txt",
                "README.md", 
                ".env.example",
                "Dockerfile",
                "setup.sh"
            ]
            
            # Add main files
            for file_path in files_to_include:
                full_path = f"{base_path}/{file_path}"
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        core_files[file_path] = f.read()
                    print(f"Added {file_path}")
                except FileNotFoundError:
                    print(f"Warning: {file_path} not found, skipping")
                    continue
            
            # Add all src directory contents
            src_files = self._get_directory_files(f"{base_path}/src", "src")
            core_files.update(src_files)
            
            # Create .gitignore for the API project
            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
env.bak/
venv.bak/

# Environment variables
.env

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Dependencies
node_modules/
"""
            core_files['.gitignore'] = gitignore_content
            
            # Create API-specific README
            api_readme = """# AI Code Generation API

A Flask-based API for generating code using Google Gemini AI and deploying to GitHub Pages.

## Features

- Natural language to code generation using Google Gemini
- GitHub repository creation and file management
- GitHub Pages deployment
- Task-based generation with evaluation callbacks
- Static web application generation (HTML/CSS/JavaScript)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the application:
```bash
python app.py
```

## API Endpoints

- `POST /api/generate-and-deploy-task` - Generate code from task brief and deploy
- `GET /api/health` - Health check
- `GET /api/status` - Service status

## Environment Variables

- `GEMINI_API_KEY` - Google Gemini API key
- `GITHUB_TOKEN` - GitHub personal access token
- `SECRET_KEY` - Secret key for authentication

## License

MIT License
"""
            core_files['README.md'] = api_readme
            
            print(f"Total files to push: {len(core_files)}")
            
            # Create repository
            repo_info = self.create_repository(repo_name, description, private=False)
            print(f"Repository created: {repo_info['html_url']}")
            
            # Push files
            commit_result = self.add_files_to_repository(
                repo_name=repo_name,
                files=core_files,
                commit_message="Initial commit - Core AI Code Generation API"
            )
            
            print(f"Files pushed successfully. Commit SHA: {commit_result.get('commit', {}).get('sha')}")
            
            return {
                **repo_info,
                'files_count': len(core_files),
                'commit_sha': commit_result.get('commit', {}).get('sha')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to push core API to repo: {str(e)}")
            raise Exception(f"Failed to push core API to repo: {str(e)}")
    
    def _get_directory_files(self, directory_path: str, prefix: str = "") -> Dict[str, str]:
        """
        Recursively get all files from a directory.
        
        Args:
            directory_path: Path to the directory
            prefix: Prefix to add to file paths in the repo
            
        Returns:
            Dictionary of file_path -> content
        """
        files = {}
        
        try:
            import os
            for root, dirs, filenames in os.walk(directory_path):
                # Skip __pycache__ directories
                dirs[:] = [d for d in dirs if d != '__pycache__']
                
                for filename in filenames:
                    # Skip Python cache files
                    if filename.endswith('.pyc') or filename.endswith('.pyo'):
                        continue
                        
                    full_path = os.path.join(root, filename)
                    
                    # Calculate relative path from the base directory
                    rel_path = os.path.relpath(full_path, directory_path)
                    
                    # Create the repo path with prefix
                    if prefix:
                        repo_path = f"{prefix}/{rel_path}".replace("\\", "/")
                    else:
                        repo_path = rel_path.replace("\\", "/")
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            files[repo_path] = f.read()
                        print(f"Added {repo_path}")
                    except (UnicodeDecodeError, PermissionError) as e:
                        print(f"Warning: Could not read {full_path}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error reading directory {directory_path}: {e}")
            
        return files