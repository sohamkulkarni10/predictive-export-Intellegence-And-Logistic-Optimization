import pandas as pd

from transformers import pipeline



df=pd.read_csv(
"raw_news.csv"
)



model=pipeline(
"text-classification",
model="ProsusAI/finbert"
)


scores=[]


for text in df["title"]:


    try:

        r=model(text[:512])[0]


        if r["label"]=="positive":
            scores.append(1)


        elif r["label"]=="negative":
            scores.append(-1)


        else:
            scores.append(0)


    except:

        scores.append(0)



df["sentiment"]=scores



df.to_csv(
"news_sentiment.csv",
index=False
)
