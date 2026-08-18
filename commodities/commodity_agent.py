# from langchain_openai import ChatOpenAI
# from langchain_core.tools import tool
# from langgraph.prebuilt import create_react_agent

# from price_agent_tools import predict_price



# import os

# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY_HERE"

# # LLM

# llm = ChatOpenAI(
#     model="gpt-4.1-mini",
#     temperature=0
# )



# # Tool

# @tool
# def commodity_predictor(
#     total_news: int,
#     average_sentiment: float,
#     positive_news: int,
#     negative_news: int,
#     neutral_news: int,
#     news_growth: float,
#     price: float,
#     price_change: float,
#     price_pct_change: float,
#     MA7: float,
#     MA30: float
# ):
#     """
#     Predict next commodity price using trained XGBoost model.
#     """

#     data = {

#         "total_news": total_news,
#         "average_sentiment": average_sentiment,
#         "positive_news": positive_news,
#         "negative_news": negative_news,
#         "neutral_news": neutral_news,
#         "news_growth": news_growth,

#         "price": price,
#         "price_change": price_change,
#         "price_pct_change": price_pct_change,

#         "MA7": MA7,
#         "MA30": MA30
#     }


#     result = predict_price(data)

#     return f"Predicted price: {result}"



# # create agent

# agent = create_react_agent(

#     model=llm,

#     tools=[
#         commodity_predictor
#     ]

# )



# # ask agent

# response = agent.invoke(

# {
# "messages":[

# (
# "user",

# """
# Predict wheat price.

# News:
# Drought affected wheat production.
# Export restrictions increased.

# Current market:

# total_news=150
# average_sentiment=-0.35
# positive_news=20
# negative_news=90
# neutral_news=40
# news_growth=120

# price=250
# price_change=8.5
# price_pct_change=0.034
# MA7=245.5
# MA30=235.2

# """
# )

# ]

# }

# )



# print(
#     response["messages"][-1].content
# )


import os
import json
from groq import Groq

from price_agent_tools import predict_price


# =========================
# API KEY
# =========================
#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
os.environ["GROQ_API_KEY"] = "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"


client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)



# =========================
# LLM CALL
# =========================

def ask_llm(prompt):

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[

            {
                "role":"system",
                "content":
                """
                You are commodity market AI.
                Extract numeric features.
                Return only JSON.
                """
            },

            {
                "role":"user",
                "content":prompt
            }
        ]

    )

    return response.choices[0].message.content




# =========================
# AGENT
# =========================

def commodity_agent(news_text):


    prompt=f"""

Analyze this news:

{news_text}


Return JSON only:

{{
"total_news":150,
"average_sentiment":-0.3,
"positive_news":20,
"negative_news":80,
"neutral_news":50,
"news_growth":100
}}

"""


    result = ask_llm(prompt)


    print("\nGemini/Groq Analysis")
    print(result)



    # convert text to dictionary

    news_features = json.loads(
        result.replace("```json","")
             .replace("```","")
    )



    # add market features

    news_features.update({

        "price":20391,

        "price_change":-6,

        "price_pct_change":0.004,

        "MA7":20370.5,

        "MA30":20450.2

    })



    prediction = predict_price(
        news_features
    )



    print(
        "\nPredicted Future Price:",
        prediction
    )



    explanation = ask_llm(

f"""
Explain:

News:
{news_text}

Prediction:
{prediction}

Give short market reason.
"""

    )


    print("\nAI Explanation")
    print(explanation)




# =========================
# TEST
# =========================


commodity_agent(

"""
coffee production decreased because of drought.

"""

)