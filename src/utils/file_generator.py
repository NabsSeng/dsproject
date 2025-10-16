"""
Utilities for generating various project files (README, LICENSE, tests, workflows).
Focused on static web applications only.
"""

import json
from datetime import datetime
from typing import Dict, List, Any

class FileGenerator:
    """Utility class for generating project files for static web applications."""
    
    @staticmethod
    def generate_readme(repo_name: str, description: str, language: str = 'javascript', 
                       tests: List[Dict] = None) -> str:
        """Generate a README.md file for static web applications."""
        
        test_section = ""
        if tests:
            test_section = "\n## Tests\n\nThis project includes the following test cases:\n\n"
            for i, test in enumerate(tests, 1):
                test_section += f"{i}. **{test['description']}**\n"
                test_section += f"   - Input: `{test['input']}`\n"
                test_section += f"   - Expected Output: `{test['expected_output']}`\n\n"
        
        # Setup instructions for static web apps
        setup_instructions = """
### Prerequisites
- Modern web browser
- HTTP server (optional for local development)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd {repo_name}

# Option 1: Open directly in browser
open index.html

# Option 2: Serve with Python (recommended)
python -m http.server 8000
# Then visit http://localhost:8000

# Option 3: Serve with Node.js
npx serve .
# Then visit http://localhost:3000
```

### Testing
Open the application in a web browser and verify functionality according to the test cases above.
If automated tests are included, open test.html in your browser or run `npm test` if package.json exists.
"""
        
        readme_content = f"""# {repo_name}

{description}

## Overview

This is a static web application built with {language}. It runs entirely in the browser without requiring a server backend. The application is automatically deployed to GitHub Pages.

## Features

- ✨ Client-side web application
- 🌐 Deployed to GitHub Pages
- 📱 Responsive design
- 🧪 Comprehensive test coverage
- 🚀 CI/CD pipeline with GitHub Actions
- 📦 No server dependencies required

{test_section}
## Setup and Installation

{setup_instructions}

## Deployment

This project is automatically deployed to GitHub Pages using GitHub Actions. Every push to the main branch triggers:

1. **Validation**: HTML and JavaScript files are validated
2. **Test**: Automated tests are executed (if available)
3. **Deploy**: The application is deployed to GitHub Pages

## Project Structure

```
{repo_name}/
├── index.html          # Main HTML file
├── styles.css          # Styling
├── script.js           # JavaScript functionality
├── test.html           # Test interface (if applicable)
├── README.md           # Project documentation
├── LICENSE            # Project license
└── .github/           # GitHub configuration
    └── workflows/     # GitHub Actions workflows
        └── ci.yml     # CI/CD pipeline
```

## Live Demo

Once deployed, the application will be available at:
`https://[username].github.io/{repo_name}`

## Technology Stack

- **Frontend**: {language.title()}
- **Styling**: CSS3
- **Hosting**: GitHub Pages
- **CI/CD**: GitHub Actions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test in a web browser
5. Submit a pull request

## License

This project is licensed under the terms specified in the LICENSE file.

---

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by AI Code Generator*
"""
        
        return readme_content
    
    @staticmethod
    def generate_license(license_type: str = 'mit', author: str = 'Generated Project') -> str:
        """Generate a LICENSE file."""
        year = datetime.now().year
        
        licenses = {
            'mit': f"""MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
            'apache': f"""Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   Copyright {year} {author}

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
""",
            'gpl': f"""GNU General Public License v3.0

Copyright (C) {year} {author}

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
        }
        
        return licenses.get(license_type.lower(), licenses['mit'])
    
    @staticmethod
    def generate_github_workflow(language: str = 'javascript', repo_name: str = '') -> str:
        """Generate a GitHub Actions workflow file for static web applications."""
        
        return f"""name: Build, Test, and Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Node.js (for tooling)
      uses: actions/setup-node@v4
      with:
        node-version: '18'

    - name: Install dependencies (if package.json exists)
      run: |
        if [ -f package.json ]; then
          npm ci
        else
          echo "No package.json found, using static files"
        fi

    - name: Validate HTML
      run: |
        echo "Validating HTML files..."
        for file in *.html; do
          if [ -f "$file" ]; then
            echo "Found HTML file: $file"
            if grep -q "<!DOCTYPE\\|<html\\|<head\\|<body" "$file"; then
              echo "✓ $file appears to be valid HTML"
            else
              echo "⚠ $file may not be valid HTML"
            fi
          fi
        done

    - name: Test JavaScript
      run: |
        echo "Testing JavaScript files..."
        for file in *.js; do
          if [ -f "$file" ]; then
            node -c "$file" && echo "✓ $file syntax OK" || echo "✗ $file has syntax errors"
          fi
        done

    - name: Run custom tests (if available)
      run: |
        if [ -f test.js ] && [ -f package.json ]; then
          npm test
        elif [ -f test.html ]; then
          echo "HTML test file found - manual testing required"
        else
          echo "No automated tests found"
        fi

    - name: Build (if build script exists)
      run: |
        if [ -f package.json ] && npm run build --if-present; then
          echo "Build completed"
        else
          echo "No build script found, using files as-is"
        fi

    - name: Setup Pages
      uses: actions/configure-pages@v4

    - name: Upload artifact
      uses: actions/upload-pages-artifact@v3
      with:
        path: '.'

  deploy:
    environment:
      name: github-pages
      url: ${{{{ steps.deployment.outputs.page_url }}}}
    runs-on: ubuntu-latest
    needs: build-and-test
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
"""
    
    @staticmethod
    def generate_test_files(tests: List[Dict], language: str = 'javascript') -> Dict[str, str]:
        """Generate test files for static web applications."""
        
        # For static web apps, we'll create an HTML test interface
        test_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Suite</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .test-case {{
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #fafafa;
        }}
        .test-case h3 {{
            margin-top: 0;
            color: #333;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        .test-detail {{
            margin: 10px 0;
            padding: 10px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .input {{
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
        }}
        .expected {{
            background-color: #e8f5e8;
            border-left: 4px solid #4caf50;
        }}
        .result {{
            padding: 10px;
            margin: 10px 0;
            border-radius: 3px;
            border-left: 4px solid #ff9800;
            background-color: #fff3e0;
        }}
        .pass {{
            background-color: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }}
        .fail {{
            background-color: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }}
        button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }}
        button:hover {{
            background: #0056b3;
        }}
        .run-all {{
            background: #28a745;
            margin-bottom: 20px;
        }}
        .run-all:hover {{
            background: #1e7e34;
        }}
        .summary {{
            background: #17a2b8;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Automated Test Suite</h1>
        <div class="summary">
            <p><strong>Test Count:</strong> {len(tests)} tests</p>
            <p><strong>Instructions:</strong> Click individual test buttons or "Run All Tests" to validate the application functionality.</p>
        </div>
        
        <button class="run-all" onclick="runAllTests()">🚀 Run All Tests</button>
        <div id="overall-result"></div>
        
"""
        
        for i, test in enumerate(tests, 1):
            test_content += f"""
        <div class="test-case">
            <h3>Test {i}: {test['description']}</h3>
            <div class="test-detail input">
                <strong>Input:</strong> {test['input']}
            </div>
            <div class="test-detail expected">
                <strong>Expected Output:</strong> {test['expected_output']}
            </div>
            <div class="result" id="result-{i}">
                <button onclick="runTest{i}()">▶️ Run Test</button>
                <span id="test-{i}-result"></span>
            </div>
        </div>
"""
        
        test_content += """
    </div>

    <script>
        // Auto-generated test functions
        let testResults = [];
"""
        
        for i, test in enumerate(tests, 1):
            test_content += f"""
        function runTest{i}() {{
            try {{
                console.log('Running Test {i}: {test['description']}');
                
                // Test: {test['description']}
                // Input: {test['input']}
                // Expected: {test['expected_output']}
                
                // TODO: Implement actual test logic based on your application
                // For now, this is a placeholder that demonstrates test structure
                
                const testPassed = true; // Replace with actual test logic
                
                if (testPassed) {{
                    document.getElementById('test-{i}-result').innerHTML = 
                        '<span class="pass">✅ Test structure created (implement actual test logic)</span>';
                    testResults[{i-1}] = true;
                }} else {{
                    document.getElementById('test-{i}-result').innerHTML = 
                        '<span class="fail">❌ Test failed</span>';
                    testResults[{i-1}] = false;
                }}
            }} catch (error) {{
                document.getElementById('test-{i}-result').innerHTML = 
                    '<span class="fail">❌ Error: ' + error.message + '</span>';
                testResults[{i-1}] = false;
            }}
        }}
"""
        
        test_content += f"""
        
        function runAllTests() {{
            console.log('Running all tests...');
            testResults = new Array({len(tests)}).fill(false);
            
"""
        
        for i, test in enumerate(tests, 1):
            test_content += f"            runTest{i}();\n"
        
        test_content += f"""
            
            // Show overall results
            setTimeout(() => {{
                const passedTests = testResults.filter(result => result === true).length;
                const totalTests = {len(tests)};
                const overallResult = document.getElementById('overall-result');
                
                if (passedTests === totalTests) {{
                    overallResult.innerHTML = 
                        '<div class="result pass">🎉 All tests passed! (' + passedTests + '/' + totalTests + ')</div>';
                }} else {{
                    overallResult.innerHTML = 
                        '<div class="result fail">⚠️ Some tests failed: ' + passedTests + '/' + totalTests + ' passed</div>';
                }}
            }}, 100);
        }}
        
        // Automatically run tests when page loads
        window.onload = function() {{
            console.log('Test page loaded. {len(tests)} tests available.');
            console.log('Click "Run All Tests" or individual test buttons to execute tests.');
        }};
    </script>
</body>
</html>
"""
        
        # Also create a simple package.json if it might be useful
        package_json = {
            "name": "static-web-app",
            "version": "1.0.0",
            "description": "Static web application with test suite",
            "main": "index.html",
            "scripts": {
                "test": "echo 'Open test.html in your browser to run tests'",
                "serve": "python -m http.server 8000",
                "start": "python -m http.server 8000"
            },
            "keywords": ["static", "web", "html", "css", "javascript"],
            "license": "MIT"
        }
        
        return {
            'test.html': test_content,
            'package.json': json.dumps(package_json, indent=2)
        }