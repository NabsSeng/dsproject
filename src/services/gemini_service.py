"""
Google Gemini API integration for code generation.
"""

import os
import logging
import google.generativeai as genai
from typing import Dict, List, Any
from google.generativeai import types  

class GeminiCodeGenerator:
    """Service for generating code using Google Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini code generator."""
        api_key = os.getenv('GEMINI_API_KEY')

        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.logger = logging.getLogger(__name__)
    
    def generate_code_from_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate code based on task data with brief, checks, and attachments.
        
        Args:
            task_data: Task data containing brief, checks, attachments, etc.
            
        Returns:
            Dictionary containing generated files and their content
        """
        try:
            brief = task_data['brief']
            checks = task_data['checks']
            attachments = task_data.get('attachments', [])
            task_id = task_data['task']
            
            # Build the prompt for task-based generation
            prompt = self._build_task_generation_prompt(brief, checks, attachments, task_id)

            response = self.get_ai_response(prompt, model_name="gemini-2.5-flash")
            self.logger.info(f"simple call success {response}")
            self.logger.info(f"Generating code for task: {task_id} with {prompt}")
            
            # Generate code using Gemini
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise Exception("No response from Gemini API")
            
            # Parse the response to extract files
            generated_files = self._parse_generated_response(response.text, 'javascript')
            
            self.logger.info(f"Successfully generated {len(generated_files)} files for task")
            
            return {
                'files': generated_files,
                'language': 'javascript',
                'framework': 'vanilla',
                'task_id': task_id
            }
            
        except Exception as e:
            self.logger.error(f"Error generating code for task: {str(e)}")
            raise Exception(f"Task-based code generation failed: {str(e)}")

    def generate_code(self, instructions: str, language: str = 'javascript', 
                     framework: str = 'vanilla', tests: List[Dict] = None) -> Dict[str, Any]:
        """
        Generate code based on instructions and requirements.
        
        Args:
            instructions: Natural language description of what to build
            language: Programming language (javascript, python, html, etc.)
            framework: Framework to use (vanilla, react, vue, etc.)
            tests: List of test cases to consider
            
        Returns:
            Dictionary containing generated files and their content
        """
        try:
            # Build the prompt
            prompt = self._build_code_generation_prompt(instructions, language, framework, tests)
            
            self.logger.info(f"Generating code for: {instructions[:100]}...")
            
            # Generate code using Gemini
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise Exception("No response from Gemini API")
            
            # Parse the response to extract files
            generated_files = self._parse_generated_response(response.text, language)
            
            self.logger.info(f"Successfully generated {len(generated_files)} files")
            
            return {
                'files': generated_files,
                'language': language,
                'framework': framework
            }
            
        except Exception as e:
            self.logger.error(f"Error generating code: {str(e)}")
            raise Exception(f"Code generation failed: {str(e)}")
    
    def _build_task_generation_prompt(self, brief: str, checks: List[str], 
                                     attachments: List[Dict], task_id: str) -> str:
        """Build the prompt for task-based code generation."""
        
        check_requirements = "\n\nEvaluation Requirements (MUST be satisfied):\n"
        for i, check in enumerate(checks, 1):
            check_requirements += f"{i}. {check}\n"
        
        attachment_info = ""
        if attachments:
            attachment_info = "\n\nAttachments provided:\n"
            for attachment in attachments:
                attachment_info += f"- {attachment['name']}: {attachment['url'][:100]}...\n"
            attachment_info += "\nUse these attachments in your implementation as needed.\n"
        
        prompt = f"""
You are an expert frontend web developer. Generate a complete, functional client-side web application for this specific task:

TASK ID: {task_id}
BRIEF: {brief}

{check_requirements}
{attachment_info}

CRITICAL CONSTRAINTS:
- Generate ONLY client-side code (HTML, CSS, JavaScript)
- NO server-side code whatsoever
- All functionality must work in a web browser without a server
- Must be deployable to GitHub Pages (static hosting only)
- Handle URL parameters (e.g., ?url=...) using JavaScript
- Use fetch() API for any external requests (if allowed by CORS)
- Include error handling for all operations

SPECIFIC REQUIREMENTS:
1. Generate COMPLETE, WORKING code - no placeholders
2. Create separate HTML, CSS, and JavaScript files
3. Implement ALL requirements from the brief
4. Ensure ALL evaluation checks can be satisfied
5. Include proper error handling and user feedback
6. Make the interface responsive and user-friendly
7. Use modern JavaScript (ES6+) and CSS3
8. Include comments explaining key functionality

IMPLEMENTATION NOTES:
- If handling images, use HTML5 Canvas or image processing libraries
- For URL parameters, use URLSearchParams API
- For file uploads, use FileReader API
- Store any data in localStorage if persistence is needed
- Include loading states and error messages
- Make the UI intuitive and professional

Please structure your response as follows:
```filename: [filename]
[complete file content]
```

Generate a functional, complete CLIENT-SIDE web application that satisfies all requirements:
"""
        
        return prompt

    def _build_code_generation_prompt(self, instructions: str, language: str, 
                                    framework: str, tests: List[Dict]) -> str:
        """Build the prompt for code generation."""
        
        test_descriptions = ""
        if tests:
            test_descriptions = "\n\nTest Requirements:\n"
            for i, test in enumerate(tests, 1):
                test_descriptions += f"{i}. {test['description']}\n"
                test_descriptions += f"   Input: {test['input']}\n"
                test_descriptions += f"   Expected Output: {test['expected_output']}\n"
        
        prompt = f"""
You are an expert frontend web developer. Generate a complete, functional client-side web application based on the following instructions:

Instructions: {instructions}

Language: {language}
Framework: {framework}

{test_descriptions}

IMPORTANT CONSTRAINTS:
- Generate ONLY client-side code (HTML, CSS, JavaScript)
- NO server-side code (no Node.js, Python, PHP, etc.)
- NO backend APIs or databases
- Use local storage for data persistence if needed
- All functionality must work in a web browser without a server
- The application must be deployable to GitHub Pages (static hosting)

Requirements:
1. Generate COMPLETE, WORKING code - no placeholders or comments like "// Add your code here"
2. Include ALL necessary files for a functional web application
3. Create separate HTML, CSS, and JavaScript files
4. Include proper error handling and validation
5. Make the code production-ready and well-structured
6. Ensure the code can pass the specified tests
7. Use vanilla JavaScript or the specified framework
8. Include responsive design with CSS

Please structure your response as follows:
```filename: [filename]
[complete file content]
```

For each file, use the format above. Start with index.html, then styles.css, then script.js or main.js.

Generate a functional, complete CLIENT-SIDE web application now:
"""
        
        return prompt
    
    def _parse_generated_response(self, response_text: str, language: str) -> Dict[str, str]:
        """Parse the generated response to extract individual files."""
        files = {}
        
        # Split by code blocks
        lines = response_text.split('\n')
        current_file = None
        current_content = []
        in_code_block = False
        
        for line in lines:
            # Check for filename declaration
            if line.startswith('```filename:') or line.startswith('filename:'):
                if current_file and current_content:
                    # Save previous file
                    files[current_file] = '\n'.join(current_content).strip()
                
                # Extract filename
                current_file = line.replace('```filename:', '').replace('filename:', '').strip()
                current_content = []
                in_code_block = False
                continue
            
            # Check for code block start/end
            if line.startswith('```'):
                if not in_code_block and current_file:
                    in_code_block = True
                elif in_code_block and current_file:
                    # End of code block, save file
                    files[current_file] = '\n'.join(current_content).strip()
                    current_file = None
                    current_content = []
                    in_code_block = False
                continue
            
            # Add content to current file
            if current_file and (in_code_block or not line.startswith('```')):
                current_content.append(line)
        
        # Save last file if exists
        if current_file and current_content:
            files[current_file] = '\n'.join(current_content).strip()
        
        # If no files were parsed with the structured format, try to extract code blocks
        if not files:
            files = self._extract_code_blocks_fallback(response_text, language)
        
        # Ensure we have at least one main file
        if not files:
            main_filename = self._get_main_filename(language)
            files[main_filename] = response_text.strip()
        
        return files
    
    def _extract_code_blocks_fallback(self, text: str, language: str) -> Dict[str, str]:
        """Fallback method to extract code from response."""
        files = {}
        
        # Look for code blocks
        import re
        code_blocks = re.findall(r'```(?:html|css|javascript|js|python|py)?\n(.*?)\n```', text, re.DOTALL)
        
        if code_blocks:
            main_filename = self._get_main_filename(language)
            
            # If only one code block, use it as main file
            if len(code_blocks) == 1:
                files[main_filename] = code_blocks[0].strip()
            else:
                # Multiple blocks - try to identify by content
                for i, block in enumerate(code_blocks):
                    if 'html' in block.lower() and '<!DOCTYPE' in block:
                        files['index.html'] = block.strip()
                    elif 'function' in block or 'const' in block or 'let' in block:
                        files['script.js'] = block.strip()
                    elif 'body' in block or 'div' in block:
                        files['styles.css'] = block.strip()
                    else:
                        files[f'file_{i+1}.{self._get_file_extension(language)}'] = block.strip()
        
        return files
    
    def _get_main_filename(self, language: str) -> str:
        """Get the main filename for a given language."""
        if language.lower() in ['html', 'web', 'frontend']:
            return 'index.html'
        elif language.lower() in ['javascript', 'js', 'node']:
            return 'app.js'
        elif language.lower() == 'python':
            return 'main.py'
        else:
            return f'main.{self._get_file_extension(language)}'
    
    def _get_file_extension(self, language: str) -> str:
        """Get file extension for a language."""
        extensions = {
            'javascript': 'js',
            'python': 'py',
            'html': 'html',
            'css': 'css',
            'typescript': 'ts',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c'
        }
        return extensions.get(language.lower(), 'txt')

    def get_ai_response(self, prompt: str, model_name:str) -> str:
        response=""
        response = self.model.generate_content("Short Haiku about a dragon flying over mountains")
        self.logger.info(response.text)
        return response.text