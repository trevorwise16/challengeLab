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
import base64


#Twitter Authentication keys
auth = tweepy.OAuthHandler('7m6vTJb53vcAK948l6JGRC9az'
, 'eiQNpAWnHRfKL0trqnbZjds6KGWLitipyrifiJzpYIyztH6LOs')
auth.set_access_token('879522363095822337-V7ZmrdcIYnl5jpdfAnGJrFVXHgJe6F5'
, 'bnIBXW1pvFFCyfHCppI9Bb5oW7rINP9Eop4bQ0cV7HFRl')



#API Authericator
api = tweepy.API(auth)
tone_analyzer = ToneAnalyzerV3(
    version='2017-09-21',
    iam_apikey='Q5DgsEE_FjaLYsDXLyU7-QGSQZpx2UByTYXkT4Yw1iai',
    url='https://gateway.watsonplatform.net/tone-analyzer/api'
)


# def firstThread(tracker):
#     twitterStream = Stream(auth, listener())
#     twitterStream.filter(track=tracker)


X = deque()
X.append(0)
Y = deque()
Y.append(0)
emoX = deque()
emoX.append(0)
emotions = {"sad": [0], "satisfied": [0], "frustrated": [0]}

def emotionAnalysis(txt):
    """
    Gathering emotion information using Watson API.
    """
    utterances = [{"text" : txt,
                   "user" : "Customer"}]
    utterance_analyses = tone_analyzer.tone_chat(utterances).get_result()
    for uter in utterance_analyses['utterances_tone']:
        for tones in uter['tones']:
            if tones['tone_id'] == 'sad':
                lensat = len(emotions["satisfied"])
                lenfrus = len(emotions["frustrated"])
                emotions["satisfied"].append(emotions["satisfied"][lensat-1])
                emotions["frustrated"].append(emotions["frustrated"][lenfrus - 1])
                emotions["sad"].append(tones['score'])
                emoX.append(emoX[-1] + 1)
            if tones['tone_id'] == 'satisfied':
                lensad = len(emotions["sad"])
                lenfrus = len(emotions["frustrated"])
                emotions["sad"].append(emotions["sad"][lensad - 1])
                emotions["frustrated"].append(emotions["frustrated"][lenfrus - 1])
                emotions["satisfied"].append(tones['score'])
                emoX.append(emoX[-1] + 1)
            if tones['tone_id'] == 'frustrated':
                lensat = len(emotions["satisfied"])
                lensad = len(emotions["sad"])
                emotions["satisfied"].append(emotions["satisfied"][lensat - 1])
                emotions["sad"].append(emotions["sad"][lensad - 1])
                emotions["frustrated"].append(tones['score'])
                emoX.append(emoX[-1] + 1)


class listener(StreamListener):

    total = 0
    count = 0
    mean = 0

    def on_data(self, datar):
        """
        Function that performs actions on data we've gathered.
        """
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
        print(emotions)


    def on_error(self, status):
        print("ducks")
        print (status)

def sentimentAnalysis(text):
    """
    Helper function for sentiment analysis.
    """
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def tweetGatherer(query):
    """
    Main function for gathering Tweets using a query term.
    """
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
    """
    Function for gaining average sentiment polarity of Tweets
    """
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
tracker = ["Packers"]
print(tracker)
twitterStream = Stream(auth, listener())
twitterStream.filter(track=tracker,is_async=True)

app = dash.Dash(__name__)
encoded_image = base64.b64encode(open('pkanalytics.png', 'rb').read())


"""
Python-based HTML declaration using Dash 
"""
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
            html.Button('Submit', id ='Submit'),
            html.Div(id='filler'),
            # dcc.Input(id = 'counter', value = '0', type = 'text')
        ], className="six columns"),

        html.Div([
            html.H3('Emotions'),
            dcc.Graph(id='g2', animate=True),
            dcc.Interval(
                id='graph-up',
                interval=1 * 1000
            ),
            html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode())),
        ], className="six columns"),
    ], className="row"),
])

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

#tracker = ["Packers"]
#twitterStream = Stream(auth, listener())
# t1 = threading.Thread(target = firstThread, args=tracker)
#twitterStream.filter(track=tracker)
# t1.start()



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
    [Input('Submit', 'n_clicks')],
    state=[State(component_id='search-input', component_property='value')]
    )
def runall(nclicks, value):
    """
    Used for adding queries to the data being streamed.
    """
    tracker.append(value)
    twitterStream.disconnect()
    twitterStream.filter(track=tracker, is_async=True)

    # t2 = threading.Thread(target = secondThread)
    # t2.start()
    return None

    # @app.callback(Output('live-graph', 'figure'),
    # [Input(component_id='search-input', component_property='n_submit')],
    # [State('search-input', 'value')],
    # events=[Event('graph-update', 'interval')]
    # )
    # def update_graph_scatter(ns1, input_value=None):

        # if ns1 and ns1 not in tracker:
        #     tracker.append(ns1)
@app.callback(Output('live-graph', 'figure'),
                  events=[Event('graph-update', 'interval')]
                  )
def update_graph_scatter():
    """
    Callback function for plotting sentiment polarity after gathering
    Tweet data on Dash.
    """
    data = plotly.graph_objs.Scatter(
            x=list(X),
            y=list(Y),
            name='Scatter',
            mode='lines+markers'
        )
        # print(tracker)
    return {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(X), max(X)]),yaxis=dict(range=[min(Y), max(Y)]),)}

@app.callback(Output('g2', 'figure'),
                  events=[Event('graph-up', 'interval')]
                  )
def update_emotion_scatter():
    """
    Callback function for plotting three emotions gained from
    Watson API on Dash.
    """
    trace1 = plotly.graph_objs.Scatter(
            x=list(emoX),
            y=emotions["sad"],
            name='sad',
            mode='lines+markers'
        )
    trace2 = plotly.graph_objs.Scatter(
            x=list(emoX),
            y=emotions["satisfied"],
            name='satisfied',
            mode='lines+markers'
        )
    trace3 = plotly.graph_objs.Scatter(
            x=list(emoX),
            y=emotions["frustrated"],
            name='frustrated',
            mode='lines+markers'
        )
    data = [trace1, trace2, trace3]
        # print(tracker)
    return {'data': data, 'layout': go.Layout(xaxis=dict(range=[min(emoX), max(emoX)]),yaxis=dict(range=[min(min(emotions["sad"]), min(emotions["satisfied"]), min(emotions["frustrated"])), max(max(emotions["sad"]), max(emotions["satisfied"]), max(emotions["frustrated"]))]),)}


if __name__ == '__main__':
    app.run_server(port=8001, debug=True)
