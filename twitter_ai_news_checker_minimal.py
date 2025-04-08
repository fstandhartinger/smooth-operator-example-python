import os
import asyncio
import json
from dotenv import load_dotenv
from openai import OpenAI
from smooth_operator_agent_tools import SmoothOperatorClient, ExistingChromeInstanceStrategy

async def run_minimal_twitter_checker():
    load_dotenv()
    screengrasp_api_key = os.getenv("SCREENGRASP_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not screengrasp_api_key or not openai_api_key:
        print("Error: SCREENGRASP_API_KEY or OPENAI_API_KEY missing.")
        return

    client = SmoothOperatorClient(screengrasp_api_key)
    client.start_server()

    tweets_text = ""
    accounts = ["kimmonismus", "ai_for_success", "slow_developer"]
    is_browser_open = False   

    try:
        for account in accounts:
            url = f"https://x.com/{account}"
            if not is_browser_open:
                client.chrome.open_chrome(url)
                is_browser_open = True
                await asyncio.sleep(7) # Wait for initial load
            else:
                client.chrome.navigate(url)
                await asyncio.sleep(4) # Wait for navigation

            for _ in range(3):
                client.mouse.scroll(200, 200, 20)
                await asyncio.sleep(0.5) # Shorter delay for scrolling

            response = client.chrome.get_text()
            if response and response.result_value:
                tweets_text += response.result_value + "\n--------------------\n"
            await asyncio.sleep(0.5) # Shorter delay between accounts

        if not tweets_text.strip():
            print("Error: No tweet text retrieved.")
            return

        openai_client = OpenAI(api_key=openai_api_key)
        chat_completion = openai_client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[{
                "role": "user",
                "content": (
                    "Latest tweets from AI news accounts. Summarize topics (3 short bullet points) & rate breaking news probability (0-100) in the last hour. "
                    f"<tweets>{tweets_text}</tweets>"
                    'Answer JSON: { "summaryBulletPoints": ["p1", "p2", "p3"], "breakingNewsProbabilityInPercent": 50 }'
                )
            }]
        )
        result_text = chat_completion.choices[0].message.content
        # Pretty print the JSON result
        try:
            parsed_json = json.loads(result_text)
            print(json.dumps(parsed_json, indent=4))
        except json.JSONDecodeError:
            print(result_text) # Print raw text if not valid JSON

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.stop_server()

if __name__ == "__main__":
    asyncio.run(run_minimal_twitter_checker()) 