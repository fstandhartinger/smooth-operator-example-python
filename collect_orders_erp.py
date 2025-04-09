import os
import asyncio
import json
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
from openai import OpenAI
from smooth_operator_agent_tools import SmoothOperatorClient, ExistingChromeInstanceStrategy

# Order data classes for deserializing OpenAI responses
class OrderedArticle:
    def __init__(self, article_name: str, quantity: int, price_per_unit: float):
        self.article_name = article_name
        self.quantity = quantity
        self.price_per_unit = price_per_unit

class Order:
    def __init__(self, customer_name: str, ordered_articles: List[OrderedArticle]):
        self.customer_name = customer_name
        self.ordered_articles = ordered_articles

class ErpElementIds:
    def __init__(self, element_id_customer_name: str, element_id_article_name: str, 
                 element_id_quantity: str, element_id_price_per_unit: str,
                 element_id_add_item_button: str, element_id_save_order_button: str):
        self.element_id_customer_name = element_id_customer_name
        self.element_id_article_name = element_id_article_name
        self.element_id_quantity = element_id_quantity
        self.element_id_price_per_unit = element_id_price_per_unit
        self.element_id_add_item_button = element_id_add_item_button
        self.element_id_save_order_button = element_id_save_order_button

async def get_order_screenshot_from_gmail(client: SmoothOperatorClient):
    """
    Get a screenshot of an order email from Gmail.
    
    Example Email Content to send to your Gmail for testing:
    
    Subject: New Computerstuff.com Order
    Text:
    Dear you,
    
    I just visited our customer Smith & Co. Ltd.
    They want to order:
    
    - Product Name: High-Speed Router X200
      Quantity: 5 units
      Price per unit: 120.00
    
    - Product Name: Cat6 Ethernet Cable (10m)
      Quantity: 10 units
      Price per unit: 15.00
    
    Best regards,
    John Doe
    Sales Representative
    """
    print("Opening Gmail in Chrome...")
    # Use ForceClose strategy to handle existing instances
    open_result = client.chrome.open_chrome("https://mail.google.com/", 
                                           ExistingChromeInstanceStrategy.FORCE_CLOSE)
    print(open_result.message)
    if open_result.message.startswith('Error'):
        return None
    
    # Give Gmail time to load and potentially log in
    await asyncio.sleep(10)  
    
    print("Searching for 'order' in Gmail...")
    # Try to find and click the search bar
    client.mouse.click_by_description("the search mail input field")  # Adjust description if needed
    await asyncio.sleep(1)
    client.keyboard.type("New Computerstuff.com Order")
    await asyncio.sleep(0.5)
    client.keyboard.press("Enter")
    await asyncio.sleep(5)  # Wait for search results
    
    print("Clicking the first email in the search results...")
    # Click the first email result - adjust description if needed
    client.mouse.click_by_description("the first email result in the list")
    await asyncio.sleep(5)  # Wait for email to load
    
    print("Taking screenshot of the email...")
    screenshot = client.screenshot.take()
    return screenshot

async def get_order_screenshot_from_outlook(client: SmoothOperatorClient):
    """Get a screenshot of an order email from Outlook."""
    print("Opening Outlook...")
    try:
        client.system.open_application("outlook")
        await asyncio.sleep(10)  # Give Outlook time to load
    except Exception as ex:
        print(f"Failed to open Outlook: {ex}. Make sure Outlook is installed.")
        return None
    
    print("Searching for 'order' in Outlook...")
    # Using keyboard shortcuts for search
    client.keyboard.press("Ctrl+E")  # Focus search bar shortcut
    await asyncio.sleep(2)
    client.keyboard.type("New Computerstuff.com Order")
    await asyncio.sleep(5)
    client.keyboard.press("Enter")
    await asyncio.sleep(5)  # Wait for search results
    
    print("Clicking the first email in the Outlook search results...")
    # Click the first email - adjust description if needed
    client.mouse.click_by_description("the first email shown in the list pane")
    await asyncio.sleep(5)  # Wait for email to load
    
    print("Taking screenshot of Outlook...")
    screenshot = client.screenshot.take()
    return screenshot

async def download_mock_erp() -> Optional[str]:
    """Download the mock ERP application."""
    download_url = "https://www.dropbox.com/scl/fi/4qc9w57zrmmisyqu3ojnp/mini-erp-mock.exe?rlkey=x5m3ob810zt1scf0mpfn15l4v&dl=1"
    temp_dir = tempfile.gettempdir()
    file_name = "mini-erp-mock.exe"
    destination_path = os.path.join(temp_dir, file_name)
    
    if os.path.exists(destination_path):
        print("Mock ERP already exists, skipping download.")
        return destination_path
    
    try:
        import httpx
        print(f"Downloading mock ERP application to {destination_path}...")
        
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(download_url)
            response.raise_for_status()
            
            with open(destination_path, 'wb') as f:
                f.write(response.content)
                
        return destination_path
    except Exception as ex:
        print(f"Error downloading mock ERP: {ex}")
        return None

async def parse_order_data_from_screenshot(screenshot, openai_api_key):
    """Extract order data from screenshot using OpenAI."""
    if not openai_api_key:
        print("No OpenAI API key provided, skipping order extraction.")
        return None
        
    print("Asking OpenAI to extract order data from screenshot...")
    try:
        client = OpenAI(api_key=openai_api_key)
        
        prompt = """Extract the order details from the email in the screenshot. Provide the output strictly in the following JSON format:
{
  "customerName": "name of the customer",
  "orderedArticles": [
    {
      "articleName": "name of the article",
      "quantity": quantity_as_number,
      "pricePerUnit": price_as_number
    }
    // ... more articles if present
  ]
}"""

        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{screenshot.image_base64}"
                            }
                        }
                    ]
                }
            ]
        )
        
        json_response = chat_completion.choices[0].message.content
        print(f"OpenAI Order Extraction Response: {json_response}")
        
        # Parse the JSON response into our order class
        order_data = json.loads(json_response)
        
        # Create Order object with OrderedArticle objects
        ordered_articles = []
        for article_data in order_data.get("orderedArticles", []):
            article = OrderedArticle(
                article_name=article_data.get("articleName", ""),
                quantity=int(article_data.get("quantity", 0)),
                price_per_unit=float(article_data.get("pricePerUnit", 0.0))
            )
            ordered_articles.append(article)
            
        order = Order(
            customer_name=order_data.get("customerName", ""),
            ordered_articles=ordered_articles
        )
        
        print(f"Successfully extracted order for customer: {order.customer_name}")
        return order
        
    except Exception as ex:
        print(f"Error calling OpenAI for order extraction: {ex}")
        return None

async def identify_erp_element_ids(client, window_details_json, openai_api_key):
    """Use OpenAI to identify the element IDs in the ERP UI."""
    if not openai_api_key:
        print("No OpenAI API key provided, skipping element ID identification.")
        return None
        
    print("Asking OpenAI to identify ERP element IDs...")
    try:
        openai_client = OpenAI(api_key=openai_api_key)
        
        prompt = f"""Based on the following UI automation tree JSON for the 'Mini ERP Mock' application, identify the element IDs for the specified controls. Provide the output strictly in the following JSON format:
{{
  "elementIdCustomerName": "ID_for_customer_name_input",
  "elementIdArticleName": "ID_for_article_name_input",
  "elementIdQuantity": "ID_for_quantity_input",
  "elementIdPricePerUnit": "ID_for_price_input",
  "elementIdAddItemButton": "ID_for_add_item_button",
  "elementIdSaveOrderButton": "ID_for_save_order_button"
}}

UI Automation Tree JSON:
{window_details_json}"""

        chat_completion = openai_client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        json_response = chat_completion.choices[0].message.content
        print(f"OpenAI Element ID Response: {json_response}")
        
        # Parse the JSON response
        element_ids_data = json.loads(json_response)
        
        # Create ErpElementIds object
        element_ids = ErpElementIds(
            element_id_customer_name=element_ids_data.get("elementIdCustomerName", ""),
            element_id_article_name=element_ids_data.get("elementIdArticleName", ""),
            element_id_quantity=element_ids_data.get("elementIdQuantity", ""),
            element_id_price_per_unit=element_ids_data.get("elementIdPricePerUnit", ""),
            element_id_add_item_button=element_ids_data.get("elementIdAddItemButton", ""),
            element_id_save_order_button=element_ids_data.get("elementIdSaveOrderButton", "")
        )
        
        if not element_ids.element_id_customer_name:
            print("Error: Could not find necessary element IDs")
            return None
            
        print("Successfully identified ERP element IDs.")
        return element_ids
        
    except Exception as ex:
        print(f"Error calling OpenAI for element ID extraction: {ex}")
        return None

async def run_collect_orders_erp():
    """Main function to run the email-to-ERP example."""
    print("Starting Email-to-ERP Example...")
    
    # Load environment variables from .env file
    load_dotenv()
    
    screengrasp_api_key = os.getenv("SCREENGRASP_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not screengrasp_api_key:
        print("Error: SCREENGRASP_API_KEY not found in .env file. Get a free key at https://screengrasp.com/api.html")
        input("Press Enter to exit.")
        return
        
    if not openai_api_key:
        print("Warning: OPENAI_API_KEY not found in .env file. OpenAI part will be skipped. Get a key at https://platform.openai.com/api-keys")
    
    # Initialize the Smooth Operator Client
    client = SmoothOperatorClient(screengrasp_api_key)
    
    print("Starting server (can take a while, especially on first run, because it's installing the server)...")
    client.start_server()
    
    email_screenshot = None
    try:
        # --- Get Order Email Screenshot ---
        # By default, uses Gmail via Chrome.
        # To use local Outlook instead (if installed), comment the Gmail line and uncomment the Outlook line below.
        print("Attempting to get order email screenshot via Gmail...")
        email_screenshot = await get_order_screenshot_from_gmail(client)
        # print("Attempting to get order email screenshot via Outlook...")
        # email_screenshot = await get_order_screenshot_from_outlook(client)
        
        if not email_screenshot or not email_screenshot.success:
            print("Error: Could not get email screenshot.")
            return
        print("Successfully captured email screenshot.")
        
    except Exception as ex:
        print(f"Error getting email screenshot: {ex}")
        return
    
    # --- Download and Run Mock ERP ---
    erp_exe_path = None
    try:
        print("Downloading mock ERP application...")
        erp_exe_path = await download_mock_erp()
        print(f"Mock ERP downloaded to: {erp_exe_path}")
        
        print("Launching mock ERP application...")
        client.system.open_application(erp_exe_path)
        await asyncio.sleep(5)  # Give the app time to start
        print("Mock ERP application launched.")
        
    except Exception as ex:
        print(f"Error with mock ERP application: {ex}")
        # Continue even if ERP fails
    
    # --- Extract Order Data using AI ---
    order_data = None
    if openai_api_key and email_screenshot and email_screenshot.success:
        order_data = await parse_order_data_from_screenshot(email_screenshot, openai_api_key)
    else:
        print("Skipping AI order extraction (OpenAI key missing or screenshot failed).")
    
    # --- Automate ERP Data Entry ---
    if openai_api_key and order_data and erp_exe_path:
        print("Attempting to automate data entry into mock ERP...")
        try:
            # 1. Get Overview and Find ERP Window
            print("Getting system overview...")
            overview = client.system.get_overview()
            
            window_details_json = None
            
            if (overview.focus_info and 
                overview.focus_info.focused_element_parent_window and 
                overview.focus_info.focused_element_parent_window.title == "ERP system"):
                window_details_json = overview.focus_info.focused_element_parent_window.to_json_string()
            else:
                # Find the ERP window by title
                erp_window = next((w for w in overview.windows 
                                  if w.title and "ERP system" in w.title.lower()), None)
                
                if not erp_window:
                    print("Error: Could not find the Mock ERP window.")
                    return
                    
                print(f"Found Mock ERP window: {erp_window.id} - {erp_window.title}")
                
                print("Getting ERP window details...")
                window_details = client.system.get_window_details(erp_window.id)
                if not window_details or not window_details.user_interface_elements:
                    print("Error: Could not get details for the Mock ERP window.")
                    return
                    
                window_details_json = window_details.to_json_string()
            
            # 2. Get Element IDs using AI
            erp_element_ids = await identify_erp_element_ids(client, window_details_json, openai_api_key)
            if not erp_element_ids:
                print("Error: Could not identify ERP element IDs.")
                return
            
            # 3. Enter Data using Automation
            print(f"Entering customer name: {order_data.customer_name} into element {erp_element_ids.element_id_customer_name}")
            client.automation.set_value(erp_element_ids.element_id_customer_name, order_data.customer_name)
            await asyncio.sleep(0.5)  # Small delay between actions
            
            for article in order_data.ordered_articles:
                print(f"Entering article: {article.article_name}")
                client.automation.set_value(erp_element_ids.element_id_article_name, article.article_name)
                await asyncio.sleep(0.2)
                client.automation.set_value(erp_element_ids.element_id_quantity, str(article.quantity))
                await asyncio.sleep(0.2)
                client.automation.set_value(erp_element_ids.element_id_price_per_unit, f"{article.price_per_unit:.2f}")
                await asyncio.sleep(0.2)
                
                print("Clicking 'Add Item' button...")
                client.automation.invoke(erp_element_ids.element_id_add_item_button)
                await asyncio.sleep(1)  # Delay after adding item
            
            print("Clicking 'Save Order' button...")
            client.automation.invoke(erp_element_ids.element_id_save_order_button)
            await asyncio.sleep(0.5)
            
            print("Data entry automation complete.")
            
        except Exception as ex:
            print(f"Error during ERP data entry automation: {ex}")
    else:
        print("Skipping ERP data entry (AI steps failed or ERP not running).")
    
    # Ensure the server is stopped even if errors occur
    print("Stopping server...")
    client.stop_server()
    
    print("\nEmail-to-ERP Example finished. Press Enter to exit.")
    input()

if __name__ == "__main__":
    asyncio.run(run_collect_orders_erp()) 