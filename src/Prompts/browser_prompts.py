# def generate_browser_task(scenario: str) -> str:
#     """Generate the browser task prompt for executing Gherkin scenarios"""
#     return f"""
#     Execute the following Gherkin scenario with comprehensive logging and detailed actions.
#     For each interactive element you encounter, use the "Get XPath of element using index" action 
#     to capture its XPath. Get the XPath BEFORE performing any actions on the element.
#     Capture element selectors, properties, and states during execution.
    
#     {scenario}
#     """

def generate_browser_task(scenario: str) -> str:
    """Generate the browser task prompt for executing Gherkin scenarios"""
    return f"""
    Execute the following Gherkin scenario efficiently with focused actions.
    
    Important guidelines:
    1. Follow all navigation steps carefully, paying attention to URL changes between pages
    2. Verify the URL when navigating to new pages to ensure correct navigation
    3. Use the "Get XPath of element using index" action for elements you need to interact with
    4. For any links that navigate to new pages, verify that navigation was successful
    5. Be thorough in testing features on each page you navigate to
    6. Be concise in your reasoning but thorough in test coverage
    
    {scenario}
    """