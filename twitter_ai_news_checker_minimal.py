import os
import asyncio
import json
from dotenv import load_dotenv
from openai import OpenAI
from smooth_operator_agent_tools import SmoothOperatorClient

# this is just to show how short & minimalistic the code can be.
# for production use you should add some error handling, logging etc.

async def get_openai_summary(tweets_text, api_key):
    """Calls OpenAI API to summarize tweets and returns the JSON result."""
    openai_client = OpenAI(api_key=api_key)
    chat_completion = openai_client.chat.completions.create(
        model="gpt-4o", response_format={"type": "json_object"},
        messages=[{
            "role": "user",
            "content": f"Latest tweets from AI accounts. Summarize topics (3 short bullet points) & rate breaking news probability (0-100) in the last hour. <tweets>{tweets_text}</tweets> Answer JSON: {{ \"summaryBulletPoints\": [\"p1\", \"p2\", \"p3\"], \"breakingNewsProbabilityInPercent\": 50 }}"
        }]
    )
    try:
        return json.dumps(json.loads(chat_completion.choices[0].message.content), indent=4)
    except json.JSONDecodeError:
        return chat_completion.choices[0].message.content # Return raw if not JSON

async def run_minimal_twitter_checker():
    load_dotenv()
    screengrasp_key, openai_key = os.getenv("SCREENGRASP_API_KEY"), os.getenv("OPENAI_API_KEY")
    client = SmoothOperatorClient(screengrasp_key)
    client.start_server()
    tweets_text = ""
    accounts = ["sama", "datachaz", "kimmonismus", "ai_for_success", "slow_developer"]    
    for i, account in enumerate(accounts):
        if i == 0:
            client.chrome.open_chrome(f"https://x.com/{accounts[i]}") # assumes currently no other chrome browser open, otherwise won't work
        else:
            client.chrome.navigate(f"https://x.com/{accounts[i]}")
        for _ in range(3): client.mouse.scroll(200, 200, 20);
        response = client.chrome.get_text()
        if response and response.result_value: tweets_text += response.result_value + "\n"
    print(await get_openai_summary(tweets_text, openai_key))

if __name__ == "__main__":
    asyncio.run(run_minimal_twitter_checker()) 