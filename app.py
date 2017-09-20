from flask import Flask
from flask_pymongo import PyMongo
from flask import request
from flask import make_response
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from stop_words import get_stop_words
import string

import json
import os

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'bankfaq'
app.config["MONGO_URI"] = "mongodb://admin:admin@ds111204.mlab.com:11204/bankfaq"
mongo = PyMongo(app)
with app.app_context():
    credit_card_faqs = mongo.db["credit_card_faqs"]


es=Elasticsearch(['https://elastic:EN4lg3zOIkOKLdlXTW0uUAni@8f5ebcde1b08e3982834f35fa8212f67.ap-southeast-1.aws.found.io:9243/'])
#constants
INDEX_NAME="bank_data"
TYPE="faqs"



def check_db():
    for faq in credit_card_faqs.find():

        doc={
            '_op_type':'update',
            '_index':INDEX_NAME,
            '_type':TYPE,
            '_id': str(faq["_id"]),

            "doc":{
                'text': faq['answer']
            },
            "doc_as_upsert":True



        }
        yield (doc)
bulk(es,check_db(),stats_only=True,raise_on_error=False)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    print('Request:', json.dumps(req, indent=4))
    # context=req.get("contexts").get("name")
    result = req.get("result")
    parameters = result.get("parameters")
    query = ""
    for key, value in parameters.items():
        query = query + " " + value

    query = query.lower()
    query = query.translate({ord(c): None for c in string.punctuation})
    tokenized_query = query.split()
    stop_words = get_stop_words("en")
    for i in range(len(stop_words)):
        stop_words[i] = stop_words[i].translate({ord(c): None for c in string.punctuation})
        if stop_words[i] in tokenized_query:
            # query=query.replace(stop_words[i],"")
            tokenized_query.remove(stop_words[i])

    final_query = " ".join(tokenized_query)
    print(final_query)
    result = es.search(index=INDEX_NAME, doc_type=TYPE, body={"query": {"match": {"text": final_query.strip()}}})

    if result.get('hits') is not None and len(result['hits'].get('hits')) is not 0:
        print(result.get('hits'))
        print(result['hits'].get('hits'))
        response=(result['hits']['hits'][0]['_source']['text'])
    else:
        response="I could not quite comprehend it!Could you be any more vague?!!!"


    #response = tf_idf_score(query, documents)
    print(response)

    res = {
        "speech": response,
        "displayText": response,
        # "data": data,
        # "contextOut": [],
        "source": "bank_webhook"
    }
    res = json.dumps(res, indent=4)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
