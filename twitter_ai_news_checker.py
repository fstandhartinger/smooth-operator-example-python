import os
import asyncio
import json
from dotenv import load_dotenv
from openai import OpenAI
from smooth_operator_agent_tools import SmoothOperatorClient, ExistingChromeInstanceStrategy

async def run_twitter_checker():

    # Load environment variables from .env file
    load_dotenv()

    screengrasp_api_key = os.getenv("SCREENGRASP_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not screengrasp_api_key:
        print("Error: SCREENGRASP_API_KEY not found in .env file or environment variables. Get a free key at https://screengrasp.com/api.html")
        input("Press Enter to exit.")
        return

    if not openai_api_key:
        print("Warning: OPENAI_API_KEY not found in .env file or environment variables. OpenAI part will be skipped. Get a key at https://platform.openai.com/api-keys")

    # Initialize the Smooth Operator Client
    client = SmoothOperatorClient(screengrasp_api_key)

    print("Starting server (can take a while, especially on first run, because it's installing the server)...")
    # StartServer ensures the Smooth Operator server process is running in the background.
    client.start_server()

    tweets_text = ""
    is_browser_open = False
    accounts = ["kimmonismus", "ai_for_success", "slow_developer"]

    try:
        print("Opening browser...")
        for account in accounts:
            url = f"https://x.com/{account}"

            if not is_browser_open:
                open_result = client.chrome.open_chrome(url)
                print(open_result.message)
                if open_result.message.startswith('Error'):                    
                    return
                is_browser_open = True
                print("Waiting for browser to load...")
                await asyncio.sleep(7) # give the newly opened browser some time to load that page
            else:
                client.chrome.navigate(url)
                print(f"Navigated to {url}, waiting...")
                await asyncio.sleep(4) # give navigation some time

            # Scroll down the timeline
            print("Scrolling down...")
            for i in range(3):
                client.mouse.scroll(200, 200, 20) # scroll down slightly
                await asyncio.sleep(1)

            print(f"Getting text from {url}...")
            response = client.chrome.get_text()
            if response and response.result_value:
                tweets_text += response.result_value + "\n--------------------\n" # separator
            else:
                print(f"Warning: Could not get text from {url}")
            await asyncio.sleep(1) # Small delay between accounts

        if not tweets_text.strip():
             print("Error: Could not retrieve any tweet text. Skipping OpenAI analysis.")
        elif not openai_api_key:
             print("Skipping OpenAI analysis as API key is missing.")
        else:
            print("Asking OpenAI about the result...")
            try:
                openai_client = OpenAI(api_key=openai_api_key)
                chat_completion = openai_client.chat.completions.create(
                    model="gpt-4o", # Use a suitable model
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "These are the latest tweets of some twitter accounts that are typically very up-to-date on AI news. "
                                        "Give me a summary on the concrete topics they write about (3 bullet points, one short sentence, each) and a rating 0-100 if you have the impression that actual very big breaking news has just occurred within the last hour."
                                        f"<tweets>{tweets_text}</tweets>"
                                        """Answer with a JSON in this form:
                                        {
                                            "summaryBulletPoints": [
                                                "bullet point 1",
                                                "bullet point 2",
                                                "bullet point 3"
                                            ],
                                            "breakingNewsProbabilityInPercent": 50
                                        }"""
                                    )
                                }
                            ]
                        }
                    ]
                )
                result_text = chat_completion.choices[0].message.content
                print("Result:" + result_text) # Pretty print might be nice: json.dumps(json.loads(result_text), indent=4)
            except Exception as ex:
                print(f"Error calling OpenAI: {ex}")

    except Exception as e:
        print(f"An error occurred during execution: {e}")
    finally:
        # Ensure the server is stopped even if errors occur
        print("Stopping server...")
        client.stop_server() # Optional: uncomment if you want to explicitly stop the server
        pass

    print("Twitter example finished. Press Enter to exit.")
    input() # Keep console open

# To run this example directly
if __name__ == "__main__":
    asyncio.run(run_twitter_checker()) 