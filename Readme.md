# AI-Powered QA Automation Framework

A modern, AI-powered Quality Assurance (QA) automation framework that transforms user stories into executable test automation code. This framework leverages advanced AI capabilities to streamline the testing process and improve efficiency.

## 🌟 Key Features

### AI-Powered Test Generation
- Converts user stories into detailed Gherkin scenarios
- Generates both positive and negative test cases
- Covers various user flows and edge conditions

### Intelligent Browser Automation
- Automated browser interaction and test execution
- Dynamic element identification and mapping
- Comprehensive DOM detail capture
- Robust element selector generation

### Smart Code Generation
- Produces production-ready automation code
- Supports multiple testing frameworks
- Adaptive to different application architectures

## 🔧 Technology Stack

- Python
- OpenAI GPT Models
- Selenium/Playwright
- Gherkin/Cucumber
- Browser Automation Technologies

## 📦 Installation

1. Install Playwright:
```shell
playwright install
```

2. Set up the project:
```bash
# Clone the repository
git clone [your-repo-url]

# Navigate to project directory
cd [project-directory]

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file and add your OpenAI API key
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Run the application
streamlit run app.py
```

## 🖥️ Usage

1. Input your user story
2. Review and edit the generated Gherkin scenarios
3. Execute the test steps
4. Generate and review the automation code

## How It Works

1. Entry Point: User provides a story about website interactions
2. AI generates Gherkin scenarios from the user story
3. Browser context is established
4. Gherkin scenarios are parsed
5. Each scenario is executed with custom browser actions
6. Browser history is collected (XPaths, actions, content)
7. Final automation code is generated

## System Architecture

```
User Story → AI Processing → Gherkin Scenarios → Browser Automation → Code Generation
```

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See the [LICENSE](LICENSE) file for details.

## 🔄 Latest Updates

### Version 1.1.0
- Editable Gherkin Scenarios
- Save Changes functionality
- Persistent scenario storage
- Enhanced execution flow
- Improved code generation
- Updated UI with better readability
