import dash
from dash.dependencies import Output, Input, State, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
from collections import deque
import threading
import tweepy
from tweepy.streaming import StreamListener, Stream
import json
from textblob import TextBlob
import numpy as np
import newsapi
from watson_developer_cloud import ToneAnalyzerV3
import json

#Twitter Authentication keys
auth = tweepy.OAuthHandler('7m6vTJb53vcAK948l6JGRC9az'
, 'eiQNpAWnHRfKL0trqnbZjds6KGWLitipyrifiJzpYIyztH6LOs')
auth.set_access_token('879522363095822337-V7ZmrdcIYnl5jpdfAnGJrFVXHgJe6F5'
, 'bnIBXW1pvFFCyfHCppI9Bb5oW7rINP9Eop4bQ0cV7HFRl')

tracker = ["Packers"]

#API Authericator
api = tweepy.API(auth)
tone_analyzer = ToneAnalyzerV3(
    version='2017-09-21',
    iam_apikey='Q5DgsEE_FjaLYsDXLyU7-QGSQZpx2UByTYXkT4Yw1iai',
    url='https://gateway.watsonplatform.net/tone-analyzer/api'
)


def firstThread():
    twitterStream = Stream(auth, listener())
    twitterStream.filter(track=tracker)


def emotionAnalysis(txt):
    utterances = [{"text" : txt,
                   "user" : "Customer"}]
    utterance_analyses = tone_analyzer.tone_chat(utterances).get_result()
    for uter in utterance_analyses['utterances_tone']:
        for tones in uter['tones']:
            if tones['tone_id'] == 'sad':
                emotions["sad"].append(tones['score'])
            if tones['tone_id'] == 'satisfied':
                emotions["satisfied"].append(tones['score'])
            if tones['tone_id'] == 'frustrated':
                emotions["frustrated"].append(tones['score'])



X = deque()
X.append(0)
Y = deque()
Y.append(0)
emotions = {"sad": [], "satisfied": [], "frustrated": []}


class listener(StreamListener):

    total = 0
    count = 0
    mean = 0



    #This method is for what to do with the streaming data
    def on_data(self, datar):
        datad = json.loads(datar)
        #add sentiment of the text to the dictionary
        datad['sentiment'] = sentimentAnalysis(datad['text'])
        self.total += datad['sentiment']
        self.count += 1
        self.mean = self.total/self.count

        print('Average Today: ' + str(self.mean))
        X.append(X[-1] + 1)
        Y.append(self.mean)
        emotionAnalysis(datad['text'])
        print("sadness: " + str(emotions['sad']))


    def on_error(self, status):
        print("ducks")
        print (status)

def sentimentAnalysis(text):
    # analyze text of the data
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def tweetGatherer(query):
    maxTweets = 1000
    searched = []
    last_id = -1
    while len(searched) < maxTweets:
        count = maxTweets - len(searched)
        try:
            new_tweets = api.search(q=query, count=count, max_id=str(last_id - 1))
            if not new_tweets:
                break
            searched.extend(new_tweets)
            last_id = new_tweets[-1].id
        except tweepy.TweepError as e:
            # depending on TweepError.code, one may want to retry or wait
            # to keep things simple, we will give up on an error
            break
    return searched

def averageTweets(tweets):
    polarities = [sentimentAnalysis(tweet._json['text']) for tweet in tweets]
    return np.mean(polarities)

class Trends:
    api = None
    def __init__(self,api):
        self.api = api

    def getTrends(self,id=1):
        trends1 = self.api.trends_place(id)
        data = trends1[0]
        # grab the trends
        trends = data['trends']
        #print(trends)
        # grab the name from each trend
        names = [trend['name'] for trend in trends]
        return trends


"""
-----------------------------------------------------------------------------
App Functionality Coded Below Here
-----------------------------------------------------------------------------
"""
app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.Div([
        html.H3('Sentiment'),
            dcc.Graph(id='live-graph', animate=True),
            dcc.Interval(
                id='graph-update',
                interval=1 * 1000
            ),
            dcc.Input(id='search-input', value='Add a query here', type='text'),
            html.Button('Clear All Queries', id='clear-button'),
            html.Div(id='filler'),
        ], className="six columns"),

        html.Div([
            html.H3('Emotions'),
            dcc.Graph(id='g2', figure={'data': [{'y': [1, 2, 3]}]})
        ], className="six columns"),
    ], className="row")
])

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

#tracker = ["Packers"]
#twitterStream = Stream(auth, listener())
t1 = threading.Thread(target = firstThread)
#twitterStream.filter(track=tracker)
t1.start()



# @app.callback(
# Output(component_id='live-graph', component_property='figure'),
#     [Input(component_id='search-input', component_property='value')]
# )
# def set_graph_query(input_value):
#     """
#     Setting query from app input
#     """
#     query = input_value
#     tracker.append(query)

@app.callback(Output('filler', 'children'),
    [Input(component_id='clear-button', component_property='n_clicks')]
    )
def clear_queries():
    tracker = []

@app.callback(Output('live-graph', 'figure'),
[Input(component_id='search-input', component_property='n_submit')],
[State('search-input', 'value')],
events=[Event('graph-update', 'interval')]
)
def update_graph_scatter(ns1, input_value=None):
    print(Y)
    if ns1 and ns1 not in tracker:
        tracker.append(ns1)
    data = plotly.graph_objs.Scatter(
            x=list(X),
            y=list(Y),
            name='Scatter',
            mode='lines+markers'
        )
    print(tracker)
    return {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(X), max(X)]),yaxis=dict(range=[min(Y), max(Y)]),)}


if __name__ == '__main__':
    app.run_server(debug=True)
