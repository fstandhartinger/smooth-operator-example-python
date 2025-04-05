# Smooth Operator Python Client Example

This project provides a simple example of how to use the [`smooth_operator_agent_tools`](https://pypi.org/project/smooth-operator-agent-tools/#description) client library to interact with the Smooth Operator agent.

## Features

This example demonstrates:

*   Initializing the `SmoothOperatorClient`.
*   Starting the Smooth Operator background server.
*   Opening an application (Windows Calculator).
*   Using the keyboard to type input.
*   Using the mouse with ScreenGrasp to click UI elements by description.
*   Retrieving the UI automation tree of the focused window.
*   (Optional) Using the OpenAI API (GPT-4o) to interpret the automation tree and determine the application's state (e.g., the result displayed in the calculator).
*   (Optional, commented out) Taking a screenshot and using the OpenAI API to analyze it.

## Prerequisites

*   Python 3.8+
*   The Smooth Operator Agent installed and running. Download it from [https://smoothoperator.ai/](https://smoothoperator.ai/).
*   A ScreenGrasp API key. Get a free key from [https://screengrasp.com/api.html](https://screengrasp.com/api.html).
*   (Optional) An OpenAI API key if you want to use GPT-4o integration for result verification. Get a key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys).

## Setup

1.  **Clone the repository (if you haven't already):**
    ```bash
    # Navigate to the parent directory if needed
    git clone <repository-url>
    cd smooth-operator/client-libs/example-python
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API keys:**
    *   Rename the `.env.example` file to `.env`.
    *   Open the `.env` file and replace the placeholder values with your actual ScreenGrasp API key and (optionally) your OpenAI API key.

## Running the Example

Make sure the Smooth Operator Agent is running in the background.

Execute the example script:

```bash
python example.py
```

The script will:

1.  Start the Smooth Operator server connection.
2.  Open the Windows Calculator.
3.  Type "3+4".
4.  Click the "equals" button.
5.  Retrieve the calculator's UI state.
6.  If an OpenAI key is provided, it will ask GPT-4o what result is displayed.
7.  Print the result from OpenAI (if applicable).
8.  Wait for you to press Enter before exiting.

## Notes

*   The example includes pauses (`asyncio.sleep`) to allow time for applications to open and UI elements to update. You might need to adjust these timings based on your system's performance.
*   The OpenAI integration is optional. If you don't provide an API key, that part of the example will be skipped.
*   The code includes a commented-out section demonstrating how to use screenshots instead of the automation tree for analysis. Screenshots are generally less reliable and more costly in terms of API credits. 