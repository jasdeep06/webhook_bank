from flask import Flask
from flask_pymongo import PyMongo
from flask import request
from flask import make_response
from search import tf_idf_score

import json
import os
app=Flask(__name__)

app.config['MONGO_DBNAME']='bankfaq'
app.config["MONGO_URI"]="mongodb://admin:admin@ds111204.mlab.com:11204/bankfaq"
mongo=PyMongo(app)

@app.route('/webhook',methods=['POST'])
def webhook():
    req=request.get_json(silent=True,force=True)
    print('Request:',json.dumps(req,indent=4))
    #context=req.get("contexts").get("name")
    result=req.get("result")
    parameters=result.get("parameters")
    query=""
    for key,value in parameters.items():
        query=query+" "+value
    #objective=parameters.get("objective")
    credit_card_faqs=mongo.db["credit_card_faqs"]
    #credit_card_faqs.create_index([('question','text')])
    #response=credit_card_faqs.find_one({"$text":{"$search":objective[0]}})
    documents=[]
    for faq in credit_card_faqs.find():
        documents.append(faq["answer"])
        
    #print(response["answer"])
    response=tf_idf_score(query,documents)
    print(response)
    
    res={
        "speech": response,
        "displayText": response,
        # "data": data,
        # "contextOut": [],
        "source": "bank_webhook"
    }
    res=json.dumps(res,indent=4)
    r=make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')


