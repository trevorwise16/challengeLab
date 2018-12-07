import tweepy
from tweepy.streaming import StreamListener, Stream
import json
from textblob import TextBlob
import numpy as np
import newsapi


#Twitter Authentication keys
auth = tweepy.OAuthHandler('7m6vTJb53vcAK948l6JGRC9az'
, 'eiQNpAWnHRfKL0trqnbZjds6KGWLitipyrifiJzpYIyztH6LOs')
auth.set_access_token('879522363095822337-V7ZmrdcIYnl5jpdfAnGJrFVXHgJe6F5'
, 'bnIBXW1pvFFCyfHCppI9Bb5oW7rINP9Eop4bQ0cV7HFRl')



#API Authericator
api = tweepy.API(auth)




class listener(StreamListener):

    total = 0
    count = 0
    mean = 0

    #This method is for what to do with the streaming data
    def on_data(self, data):
        data = json.loads(data)
        #add sentiment of the text to the dictionary
        data['sentiment'] = sentimentAnalysis(data['text'])
        self.total += data['sentiment']
        self.count += 1
        self.mean = self.total/self.count

        print('Average Today: ' + str(self.mean))
        return(True)

    def on_error(self, status):
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
 lo
print(averageTweets(tweetGatherer('packers')))

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


#previousSentiment = averageTweets(tweetGatherer('packers'))


#newsapi = NewsApiClient(api_key='9c5c1e69af884467ac030b5ee999b9df')


# top_headlines = newsapi.get_top_headlines(q='Packers',
#                                           language='en',
#                                           country='us')
#
# print("TOP HEADLINES")
# print(top_headlines)

print("---------------------------------------------------------------------------------------------------")
print("TRENDS")
t = Trends(api)
print(t.getTrends())
#Array of words to track within the stream
print("----------------------------------------------------------------------------------------------------")

print('')
tracker = ["Packers"]
twitterStream = Stream(auth, listener())
twitterStream.filter(track=tracker)
