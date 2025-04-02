import re
import json
import asyncio
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for optimization - INCREASED LIMITS
MAX_ELEMENTS_PER_PAGE = 30  # Limit number of elements to analyze per page
MAX_TEXT_LENGTH = 150       # Truncate text content to reduce token usage
MAX_FORMS_PER_PAGE = 5      # Limit number of forms to analyze per page
MAX_FEATURES_PER_CHUNK = 8  # Process features in smaller chunks

async def analyze_element(element):
    """Extract information about an interactive element"""
    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
    element_type = tag_name
    
    # Get common attributes
    attrs = await element.evaluate("""el => {
        const attributes = {};
        for(let i = 0; i < el.attributes.length; i++) {
            const attr = el.attributes[i];
            attributes[attr.name] = attr.value;
        }
        return attributes;
    }""")
    
    # Get text content (truncated to reduce tokens)
    text_content = await element.evaluate(f"el => el.textContent.trim().substring(0, {MAX_TEXT_LENGTH})")
    
    # Determine element purpose
    element_info = {
        "tag": tag_name,
        "type": element_type,
        "attributes": attrs,
        "text": text_content
    }
    
    # For links, extract href
    if tag_name == "a" and "href" in attrs:
        element_info["href"] = attrs["href"]
        
    # For inputs, extract type and other relevant attributes
    if tag_name == "input":
        input_type = attrs.get("type", "text")
        element_info["input_type"] = input_type
        element_info["name"] = attrs.get("name", "")
        element_info["placeholder"] = attrs.get("placeholder", "")
        
    # For buttons, determine if it's a submit button
    if tag_name == "button" or (tag_name == "input" and attrs.get("type") in ["submit", "button"]):
        element_info["is_button"] = True
        if attrs.get("type") == "submit" or "submit" in text_content.lower():
            element_info["is_submit"] = True
            
    return element_info

async def analyze_form(form):
    """Extract information about a form"""
    form_info = {
        "inputs": [],
        "submit": None,
        "action": await form.evaluate("form => form.action || ''"),
        "method": await form.evaluate("form => form.method || 'get'")
    }
    
    # Get form inputs (limit to reduce token usage but increased)
    inputs = await form.query_selector_all("input, select, textarea")
    for i, input_el in enumerate(inputs):
        if i >= 8:  # Increased from 5
            break
        input_info = await analyze_element(input_el)
        form_info["inputs"].append(input_info)
        
        # Identify submit button
        if input_info.get("is_submit", False):
            form_info["submit"] = input_info
            
    # If no submit input found, look for submit buttons
    if not form_info["submit"]:
        buttons = await form.query_selector_all("button")
        for button in buttons:
            button_info = await analyze_element(button)
            if button_info.get("is_submit", False) or "submit" in button_info.get("text", "").lower():
                form_info["submit"] = button_info
                break
                
    # Try to determine form purpose
    form_text = await form.evaluate(f"form => form.textContent.substring(0, {MAX_TEXT_LENGTH})")
    form_info["likely_purpose"] = "form submission"
    
    if any(keyword in form_text.lower() for keyword in ["login", "sign in", "log in"]):
        form_info["likely_purpose"] = "login"
    elif any(keyword in form_text.lower() for keyword in ["register", "sign up", "create account"]):
        form_info["likely_purpose"] = "registration"
    elif any(keyword in form_text.lower() for keyword in ["contact", "message", "feedback"]):
        form_info["likely_purpose"] = "contact"
    elif any(keyword in form_text.lower() for keyword in ["search", "find"]):
        form_info["likely_purpose"] = "search"
        
    return form_info

async def crawl_subpage(url, discovered_pages, navigation_map, depth=0, max_depth=2):
    """Crawl a subpage and extract its structure"""
    # Skip if we've reached max depth or already visited
    if depth > max_depth or url in discovered_pages:
        return
        
    logger.info(f"Crawling subpage: {url} (depth {depth})")
    discovered_pages[url] = {"title": "", "elements": [], "forms": []}
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Set a longer timeout for page loading
            page.set_default_timeout(30000)  # 30 seconds
            
            await page.goto(url, wait_until="networkidle")
            
            # Get page title
            title = await page.title()
            discovered_pages[url]["title"] = title
            
            # Find all interactive elements (increased number to reduce token usage)
            logger.info(f"Finding interactive elements on {url}")
            interactive_elements = await page.query_selector_all('a, button, input, select, textarea')
            
            # Limit number of elements to process, but increased
            processing_count = min(len(interactive_elements), MAX_ELEMENTS_PER_PAGE)
            logger.info(f"Processing {processing_count} out of {len(interactive_elements)} elements")
            
            for i, element in enumerate(interactive_elements):
                if i >= MAX_ELEMENTS_PER_PAGE:
                    break
                    
                element_info = await analyze_element(element)
                discovered_pages[url]["elements"].append(element_info)
                
                # If it's a link to another page within the same domain, add to navigation map
                if element_info["tag"] == "a" and "href" in element_info:
                    href = element_info["href"]
                    # Check if link is relative or to the same domain
                    if href and (href.startswith('/') or href.startswith(url.split('/')[0])):
                        # Convert relative URL to absolute
                        if href.startswith('/'):
                            base_url = '/'.join(url.split('/')[:3])  # Get domain part
                            full_href = base_url + href
                        else:
                            full_href = href
                            
                        # Add to navigation map
                        navigation_map[full_href] = {"from": url, "via": element_info["text"]}
                        
                        # Recursively crawl if not yet discovered
                        if full_href not in discovered_pages and depth < max_depth:
                            await crawl_subpage(full_href, discovered_pages, navigation_map, depth + 1, max_depth)
            
            # Find forms (limited number but increased)
            logger.info(f"Finding forms on {url}")
            forms = await page.query_selector_all('form')
            
            # Limit number of forms to process but increased
            forms_to_process = min(len(forms), MAX_FORMS_PER_PAGE)
            for i in range(forms_to_process):
                try:
                    form_info = await analyze_form(forms[i])
                    discovered_pages[url]["forms"].append(form_info)
                except Exception as form_e:
                    logger.error(f"Error analyzing form {i} on {url}: {str(form_e)}")
                
            await browser.close()
            
    except Exception as e:
        logger.error(f"Error crawling {url}: {str(e)}")
        
    return

async def discover_website_structure(start_url, max_depth=2):
    """Discover the structure of a website starting from a URL"""
    logger.info(f"Starting website discovery from {start_url}")
    discovered_pages = {}
    navigation_map = {}
    
    try:
        await crawl_subpage(start_url, discovered_pages, navigation_map, depth=0, max_depth=max_depth)
    except Exception as e:
        logger.error(f"Error in website discovery: {str(e)}")
        
    return discovered_pages, navigation_map

def identify_features(discovered_pages, navigation_map, qa_agent):
    """Use AI to identify features from the discovered page structure"""
    logger.info("Identifying features from discovered pages")
    all_features = []
    
    # Process each discovered page
    for url, page_data in discovered_pages.items():
        logger.info(f"Identifying features for page: {url}")
        page_features = []
        
        # Navigation feature
        if url in navigation_map:
            nav_info = navigation_map[url]
            page_features.append({
                "type": "navigation",
                "description": f"Navigate to {page_data['title']} page",
                "from_page": nav_info["from"],
                "via_element": nav_info["via"]
            })
        
        # Form submission features (increased limit)
        for i, form in enumerate(page_data.get("forms", [])):
            if i >= MAX_FORMS_PER_PAGE:
                break
                
            form_feature = {
                "type": "form",
                "description": f"Submit {form['likely_purpose']} form",
                "inputs": form["inputs"][:5],  # Increased from 3
                "submit_button": form["submit"]
            }
            page_features.append(form_feature)
        
        # Interactive element features (increased limit)
        element_count = 0
        for element in page_data.get("elements", []):
            if element_count >= 15:  # Increased from 10
                break
                
            if element["tag"] in ["button", "input"] and element.get("type") not in ["hidden"]:
                action_feature = {
                    "type": "interaction",
                    "description": f"Interact with {element.get('text', '') or element.get('tag', 'element')}",
                    "element": element
                }
                page_features.append(action_feature)
                element_count += 1
        
        # Skip if no features found
        if not page_features:
            continue
            
        # Use AI to refine and group features - use a summary approach to reduce tokens
        logger.info(f"Using AI to refine features for {url}")
        
        # First create a compact summary of the features
        summary_prompt = f"""
        Summarize these raw page features in a compact format:
        Page title: "{page_data['title']}"
        URL: "{url}"
        Feature count: {len(page_features)}
        
        Return a brief summary in 150 words or less.
        """
        
        try:
            summary_response = qa_agent.run(summary_prompt)
            
            # Now use the summary to identify key features - INCREASED NUMBER
            feature_prompt = f"""
            Given this page summary: "{summary_response.content}"
            
            Identify 5-8 main features for testing on this page. Be comprehensive and include edge cases.
            
            Return a JSON array where each item has:
            1. "name": A descriptive name for the feature (max 10 words)
            2. "type": Either "navigation", "form", "interaction", "validation", or "content"
            3. "description": What user goal this feature serves (max 15 words)
            4. "edge_cases": Array of 1-3 potential edge cases to test (optional)
            
            Include at least one validation feature if forms are present.
            """
            
            feature_response = qa_agent.run(feature_prompt)
            try:
                # Try to parse as JSON
                refined_features = json.loads(feature_response.content)
            except:
                # If parsing fails, create a simple feature list
                logger.warning(f"Could not parse AI response as JSON for {url}")
                refined_features = [{
                    "name": f"Page: {page_data['title']}",
                    "type": "content",
                    "description": f"View and interact with {page_data['title']}",
                    "edge_cases": ["Page loads with missing content", "Page loads with network issues"]
                }]
            
            for feature in refined_features:
                feature["page_url"] = url
                feature["page_title"] = page_data["title"]
                all_features.append(feature)
                
        except Exception as e:
            logger.error(f"Error processing AI response for {url}: {str(e)}")
    
    return all_features

def generate_scenarios_from_features(all_features, navigation_map, qa_agent):
    """Generate Gherkin scenarios from identified features"""
    logger.info("Generating Gherkin scenarios from features")
    
    # Group features by page
    features_by_page = {}
    for feature in all_features:
        url = feature["page_url"]
        if url not in features_by_page:
            features_by_page[url] = []
        features_by_page[url].append(feature)
    
    # Process in smaller chunks to avoid token limits but generate more scenarios
    all_scenarios = []
    page_urls = list(features_by_page.keys())
    
    # Process 1 page at a time for more detailed scenarios
    for i in range(0, len(page_urls)):
        url = page_urls[i]
        chunk_features = {url: features_by_page[url]}
        chunk_nav = {}
        
        # Add relevant navigation paths for this page
        for target, path in navigation_map.items():
            if path["from"] == url or target == url:
                chunk_nav[target] = path
    
        # Generate scenarios for this page
        logger.info(f"Generating scenarios for page {i+1} of {len(page_urls)}: {url}")
        
        # Generate a prompt for comprehensive scenario creation
        prompt = f"""
        Generate comprehensive Gherkin scenarios for this page of a website:
        
        PAGE URL: {url}
        PAGE TITLE: {features_by_page[url][0]["page_title"]}
        
        FEATURES:
        {json.dumps(features_by_page[url], indent=2)}
        
        Requirements:
        1. Create 3-5 scenarios per feature including edge cases
        2. For forms, include:
           - Happy path with valid data
           - Negative tests with invalid data
           - Required field validation
           - Format validation (where applicable)
           - Boundary values testing
        3. For navigation, include:
           - Proper navigation steps
           - URL verification
           - Page content verification
        4. For interactions, include:
           - Expected state changes
           - Visual feedback verification
        5. Use appropriate tags to organize scenarios
        6. Format: valid Gherkin with Feature, Scenario, Given, When, Then
        7. Be thorough and comprehensive to ensure maximum test coverage
        
        IMPORTANT: Each scenario should include detailed steps with specific test data.
        """
        
        try:
            response = qa_agent.run(prompt)
            all_scenarios.append(response.content)
        except Exception as e:
            logger.error(f"Error generating scenarios for page {url}: {str(e)}")
            all_scenarios.append(f"""
            Feature: Error in scenario generation for {url}
            
            Scenario: Error generating scenarios for page
              Given I encountered an error
              When generating scenarios
              Then manual review is needed
              
            # Error: {str(e)}
            """)
    
    # Combine all scenario chunks
    combined_scenarios = "\n\n".join(all_scenarios)
    return combined_scenarios 