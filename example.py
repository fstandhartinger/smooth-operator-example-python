import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from smooth_operator_agent_tools import SmoothOperatorClient

async def main():
    # Load environment variables from .env file
    load_dotenv()

    screengrasp_api_key = os.getenv("SCREENGRASP_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not screengrasp_api_key:
        raise ValueError("SCREENGRASP_API_KEY not found in .env file. Get a free key at https://screengrasp.com/api.html")

    if not openai_api_key:
        print("Warning: OPENAI_API_KEY not found in .env file. OpenAI part will be skipped. Get a key at https://platform.openai.com/api-keys")

    # Start the Smooth Operator server and perform actions
    client = SmoothOperatorClient(screengrasp_api_key)
    print("Starting server (can take a while, especially on first run, because it's installing the server)...")
    client.start_server()

    try:
        # Start the windows calculator and calculate 3+4
        print("Opening calculator...")
        client.system.open_application("calc")
        
        print("Typing 3+4...")
        client.keyboard.type("3+4") # assumes the calc app is focused
        
        print("Clicking equals sign...")        
        # Using AI vision to find and click th equals button - alternatives:
        # - client.keyboard.type("=") - simpler and faster
        # - client.automation.invoke - using Windows UI Automation, a bit more complex to implement but very robust (not affected by focus changes)                        
        client.mouse.click_by_description("the equals sign")

        if openai_api_key:
            print("Getting window overview...")
            overview = client.system.get_overview() # assumes calc is focused, when debugging be aware you might be influencing which app is focused
            
            # Check if focused window info is available
            if overview.focus_info and overview.focus_info.focused_element_parent_window:
                focused_window_json = overview.focus_info.focused_element_parent_window.to_json_string()
                
                # You can use GPT-4o or other ai models for all sorts of tasks together with the Smooth Operator Agent Tools. 
                # In this case we use it to read the result of the calculator from its automation tree.
                # But it can also for example be used to decide which button to click next, what text to type, etc.
                print("Asking OpenAI about the result...")
                openai_client = OpenAI(api_key=openai_api_key)
                chat_completion = openai_client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"What result does the calculator display? You can read it from its automation tree: {focused_window_json}"
                                }
                            ]
                        }
                    ]
                )
                result_text = chat_completion.choices[0].message.content
                print(f"OpenAI Result: {result_text}")
            else:
                print("Could not get focused window information to send to OpenAI.")
        else:
            print("OpenAI key not provided, skipping result verification.")

        # Alternative using screenshot (more costly and potentially less reliable):
        # print("Taking screenshot...")
        # screenshot = client.screenshot.take()
        # if openai_api_key:
        #     print("Asking OpenAI about the screenshot...")
        #     openai_client = OpenAI(api_key=openai_api_key)
        #     chat_completion = openai_client.chat.completions.create(
        #         model="gpt-4o",
        #         messages=[
        #             {
        #                 "role": "user",
        #                 "content": [
        #                     {
        #                         "type": "text",
        #                         "text": "What result does the calculator display based on the screenshot?"
        #                     },
        #                     {
        #                         "type": "image_url",
        #                         "image_url": {
        #                             "url": f"data:image/jpeg;base64,{screenshot.base64_image}"
        #                         }
        #                     }
        #                 ]
        #             }
        #         ]
        #     )
        #     result_text = chat_completion.choices[0].message.content
        #     print(f"OpenAI Screenshot Result: {result_text}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the server is stopped even if errors occur
        print("Stopping server...")
        client.stop_server() # Optional: uncomment if you want to explicitly stop the server
        pass

    print("\nExample finished. Press Enter to exit.")
    input() # Keep console open

if __name__ == "__main__":
    asyncio.run(main()) 