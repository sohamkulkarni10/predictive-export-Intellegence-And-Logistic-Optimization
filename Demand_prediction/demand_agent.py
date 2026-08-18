"""
Groq-powered demand prediction agent.

Required files in the same folder:
    demand_agent.py
    demand_agent_tools.py
    demand_model_bundle.joblib
    .env

Install libraries:
    python -m pip install groq python-dotenv
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from groq import Groq

from demand_agent_tools import (
    predict_demand,
    recommend_top_commodities,
)


# ---------------------------------------------------------
# 1. Load environment variables from the .env file
# ---------------------------------------------------------

# BASE_DIR = Path(__file__).resolve().parent
# ENV_FILE = BASE_DIR / ".env"

GROQ_API_KEY="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"


# load_dotenv(dotenv_path=ENV_FILE)

client = Groq(api_key=GROQ_API_KEY)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile",
).strip()


# ---------------------------------------------------------
# 2. Create Groq client
# ---------------------------------------------------------

# def _client() -> Groq:
#     """
#     Create and return a Groq client.

#     The API key is read from:
#         Demand_prediction/.env
#     """

#     api_key = os.getenv("GROQ_API_KEY", "").strip()

#     if not api_key:
#         raise RuntimeError(
#             "\nGROQ_API_KEY is missing.\n\n"
#             "Create a file named .env inside the Demand_prediction folder.\n"
#             "Add this line inside the .env file:\n\n"
#             "GROQ_API_KEY=gsk_your_new_groq_key\n"
#         )

#     if not api_key.startswith("gsk_"):
#         raise RuntimeError(
#             "The GROQ_API_KEY inside .env does not appear to be valid. "
#             "A Groq key normally begins with gsk_."
#         )

#     return Groq(api_key=api_key)
def _client() -> Groq:
    return Groq(api_key=GROQ_API_KEY)

# ---------------------------------------------------------
# 3. Convert special values into JSON-compatible values
# ---------------------------------------------------------

def _json_default(value: Any) -> Any:
    """
    Convert NumPy, Pandas or other special values into
    JSON-compatible Python values.
    """

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            pass

    return str(value)


# ---------------------------------------------------------
# 4. Extract JSON returned by Groq
# ---------------------------------------------------------

def _json_from_text(text: str) -> Dict[str, Any]:
    """
    Convert Groq response text into a Python dictionary.
    """

    cleaned = (
        text.strip()
        .replace("```json", "")
        .replace("```JSON", "")
        .replace("```", "")
        .strip()
    )

    try:
        result = json.loads(cleaned)

        if not isinstance(result, dict):
            raise ValueError("Groq response must be a JSON object.")

        return result

    except json.JSONDecodeError:
        match = re.search(
            r"\{.*\}",
            cleaned,
            flags=re.DOTALL,
        )

        if not match:
            raise ValueError(
                "Groq did not return valid JSON.\n\n"
                f"Groq response:\n{text}"
            )

        result = json.loads(match.group(0))

        if not isinstance(result, dict):
            raise ValueError("Groq response must be a JSON object.")

        return result


# ---------------------------------------------------------
# 5. Send request to Groq
# ---------------------------------------------------------

def ask_groq(
    system_prompt: str,
    user_prompt: str,
    json_mode: bool = False,
) -> str:
    """
    Send prompts to Groq and return the response text.
    """

    request_data: Dict[str, Any] = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "temperature": 0,
        "max_tokens": 900,
    }

    if json_mode:
        request_data["response_format"] = {
            "type": "json_object"
        }

    try:
        response = (
            _client()
            .chat.completions
            .create(**request_data)
        )

    except Exception as error:
        raise RuntimeError(
            "Groq request failed.\n"
            "Check your API key, internet connection and Groq account.\n\n"
            f"Original error: {error}"
        ) from error

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("Groq returned an empty response.")

    return content.strip()


# ---------------------------------------------------------
# 6. Extract demand-related features from news
# ---------------------------------------------------------

def extract_news_features(
    news_text: str,
) -> Dict[str, Any]:
    """
    Ask Groq to convert commodity news into model features.
    """

    system_prompt = """
You are a commodity-demand news analyst.

Convert the supplied news into numerical features that can be
used for country and commodity demand prediction.

Return exactly one valid JSON object.
Do not return markdown.
Do not return an explanation.

Rules:
- sentiment_score must be between -1 and 1.
- shortage_flag must be either 0 or 1.
- production_drop must be either 0 or 1.
- production_rise must be either 0 or 1.
- price_increase must be either 0 or 1.
- price_decrease must be either 0 or 1.
- export_opportunity_score must be between 0 and 100.
- confidence must be between 0 and 1.
- Use 1 only when the event is clearly present.
- Otherwise use 0.
"""

    user_prompt = f"""
Analyse the following commodity news.

NEWS:
{news_text}

Return exactly this JSON structure:

{{
    "sentiment_score": 0.0,
    "shortage_flag": 0,
    "production_drop": 0,
    "production_rise": 0,
    "price_increase": 0,
    "price_decrease": 0,
    "export_opportunity_score": 0.0,
    "confidence": 0.5
}}
"""

    raw_result = ask_groq(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_mode=True,
    )

    features = _json_from_text(raw_result)

    # Validate and clean all extracted values
    cleaned_features = {
        "sentiment_score": max(
            -1.0,
            min(
                1.0,
                float(features.get("sentiment_score", 0.0)),
            ),
        ),
        "shortage_flag": int(
            bool(features.get("shortage_flag", 0))
        ),
        "production_drop": int(
            bool(features.get("production_drop", 0))
        ),
        "production_rise": int(
            bool(features.get("production_rise", 0))
        ),
        "price_increase": int(
            bool(features.get("price_increase", 0))
        ),
        "price_decrease": int(
            bool(features.get("price_decrease", 0))
        ),
        "export_opportunity_score": max(
            0.0,
            min(
                100.0,
                float(
                    features.get(
                        "export_opportunity_score",
                        0.0,
                    )
                ),
            ),
        ),
        "confidence": max(
            0.0,
            min(
                1.0,
                float(features.get("confidence", 0.5)),
            ),
        ),
    }

    return cleaned_features


# ---------------------------------------------------------
# 7. Explain prediction in simple language
# ---------------------------------------------------------

def _explain_prediction(
    query: str,
    result: Any,
) -> str:
    """
    Ask Groq to explain the machine-learning result.
    """

    system_prompt = """
You are an export-demand recommendation assistant.

Explain the supplied machine-learning result in simple language.

Important rules:
- Do not claim that the probability is an exact import quantity.
- Explain that it is a news-based demand opportunity signal.
- Mention the predicted demand direction.
- Mention the probability percentage when available.
- Give a short export recommendation.
- Mention the strongest reasons from the model result.
- Keep the answer concise and easy to understand.
"""

    serialised_result = json.dumps(
        result,
        indent=2,
        default=_json_default,
    )

    user_prompt = f"""
USER REQUEST:
{query}

MACHINE-LEARNING RESULT:
{serialised_result}
"""

    return ask_groq(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_mode=False,
    )


# ---------------------------------------------------------
# 8. Decide which demand tool should be called
# ---------------------------------------------------------

def _route_request(
    user_query: str,
) -> Dict[str, Any]:
    """
    Decide whether the user wants:
    1. One commodity prediction
    2. Top commodity recommendations
    """

    system_prompt = """
You route a demand-prediction request to one of two Python tools.

Return exactly one valid JSON object.
Do not return markdown.
Do not return an explanation.

Available actions:

1. predict_single
Use when the user asks for the demand of one commodity
in one country.

2. recommend_top3
Use when the user asks for the best, highest-demand or
top commodities for one country.

For predict_single:
- Extract the country.
- Extract the commodity.
- Copy news or event details into news_text.
- When no news is supplied, news_text must be an empty string.

For recommend_top3:
- Extract the country.
- commodity must be an empty string.
- news_text must be an empty string.
"""

    user_prompt = f"""
USER REQUEST:
{user_query}

Return exactly this JSON structure:

{{
    "action": "predict_single",
    "country": "country name",
    "commodity": "commodity name",
    "news_text": "news details"
}}
"""

    raw_route = ask_groq(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_mode=True,
    )

    route = _json_from_text(raw_route)

    action = str(
        route.get("action", "")
    ).strip().lower()

    country = str(
        route.get("country", "")
    ).strip()

    commodity = str(
        route.get("commodity", "")
    ).strip()

    news_text = str(
        route.get("news_text", "")
    ).strip()

    if action not in {
        "predict_single",
        "recommend_top3",
    }:
        raise ValueError(
            f"Unsupported agent action returned by Groq: {action}"
        )

    if not country:
        raise ValueError(
            "Please include a country name in the request."
        )

    if action == "predict_single" and not commodity:
        raise ValueError(
            "Please include a commodity name in the request."
        )

    return {
        "action": action,
        "country": country,
        "commodity": commodity,
        "news_text": news_text,
    }


# ---------------------------------------------------------
# 9. Main demand-agent function
# ---------------------------------------------------------

def run_demand_agent(
    user_query: str,
) -> Dict[str, Any]:
    """
    Understand the request, call the correct demand tool,
    and generate an explanation.
    """

    route = _route_request(user_query)

    if route["action"] == "recommend_top3":

        tool_result = recommend_top_commodities(
            country=route["country"],
            top_n=3,
        )

    else:

        news_text = route["news_text"]

        news_features = None

        if news_text:
            news_features = extract_news_features(
                news_text
            )

        tool_result = predict_demand(
            country=route["country"],
            commodity=route["commodity"],
            news_features=news_features,
        )

        if news_features is not None:
            tool_result[
                "groq_extracted_news_features"
            ] = news_features

    explanation = _explain_prediction(
        query=user_query,
        result=tool_result,
    )

    return {
        "route": route,
        "tool_result": tool_result,
        "ai_explanation": explanation,
    }


# ---------------------------------------------------------
# 10. Print the final result
# ---------------------------------------------------------

def print_result(
    result: Dict[str, Any],
) -> None:
    """
    Print tool output and Groq explanation.
    """

    print("\n" + "=" * 60)
    print("DEMAND PREDICTION TOOL RESULT")
    print("=" * 60)

    print(
        json.dumps(
            result["tool_result"],
            indent=2,
            default=_json_default,
        )
    )

    print("\n" + "=" * 60)
    print("GROQ DEMAND RECOMMENDATION")
    print("=" * 60)

    print(result["ai_explanation"])

    print("=" * 60)


# ---------------------------------------------------------
# 11. Run the agent continuously
# ---------------------------------------------------------

def main() -> None:
    print("\n" + "=" * 60)
    print("DEMAND PREDICTION AGENT")
    print("=" * 60)

    print(
        "\nExample 1:\n"
        "Predict wheat demand in Saudi Arabia next month. "
        "News: drought reduced wheat production."
    )

    print(
        "\nExample 2:\n"
        "Recommend top 3 commodities for Bangladesh next month."
    )

    print(
        "\nType exit to close the agent."
    )

    while True:
        query = input(
            "\nEnter your request: "
        ).strip()

        if query.lower() in {
            "exit",
            "quit",
            "close",
        }:
            print("\nDemand agent closed.")
            break

        if not query:
            print(
                "Please enter a demand prediction request."
            )
            continue

        try:
            result = run_demand_agent(query)
            print_result(result)

        except Exception as error:
            print("\n" + "=" * 60)
            print("ERROR")
            print("=" * 60)
            print(error)
            print("=" * 60)


if __name__ == "__main__":
    main()