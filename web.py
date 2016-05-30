from flask import Flask, render_template, request, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
import os
import sys
import requests
import operator
import re
import nltk
import json
from collections import Counter
from bs4 import BeautifulSoup
import stop_words

from rq import Queue
from rq.job import Job
from processor import conn




app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
q = Queue(connection=conn)

from models import *


@app.route('/results/<job_key>', methods=['GET'])
def get_results(job_key):
	job = Job.fetch(job_key, connection=conn)
	if job.is_finished:
		result = Result.query.filter_by(id=job.result).first()
		results = sorted(
			result.result_no_stop_words.items(),
			key=operator.itemgetter(1),
			reverse=True
			)[:10]
		return jsonify(results)
	else:
		return "Not yet!", 202



@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def get_counts():
    # get url
    data = json.loads(request.data.decode())
    url = data["url"]
    if 'http://' not in url[:7]:
        url = 'http://' + url
    # start job
    job = q.enqueue_call(
        func=count_worker, args=(url,), result_ttl=5000
    )
    # return created job id
    return job.get_id()






def count_worker(url):
	"""
	Given an URL, retrieves the URL and uses count_words_from_html to 
	derive clean word counts, saving these to the database.  
	"""
	errors = []

	# get the URL entered
	try:
		r = requests.get(url)
	except:
		err_string = "Unable to fetch url %s" % url
		errors.append(err_string)
		return {"error": errors}

	(raw_counts, stop_removed_count) = count_words_from_html(r)

	# store results in the database
	try:
		db_result = Result(
			url=url,
			result_all=raw_counts,
			result_no_stop_words=stop_removed_count
			)
		db.session.add(db_result)
		db.session.commit()
		return db_result.id
	except Exception as e:
		err = "Unable to add results to the database: %s" % e
		errors.append(err)
		return {"error": errors}


def count_words_from_html(page):
	"""
	Given a returned page from the requests library, this method 
	extracts the raw text using BeautifulSoup, tokenizes, removes
	punctuation, and tabulates the raw result and the result with
	common English stop words removed, and returns a tuple of results
	"""
	raw = BeautifulSoup(page.text, 'html.parser').get_text()
	nltk.data.path.append('./nltk_data') # set path for precompiled tokenizers
	tokens = nltk.word_tokenize(raw)
	text = nltk.Text(tokens)

	# remove punctuation
	nonPunct = re.compile('.*[A-Za-z].*')
	raw_words = [w for w in text if nonPunct.match(w)]
	raw_word_counts = Counter(raw_words)

	# remove English stop words
	stops = stop_words.get_stop_words('english')
	no_stop_words = [w for w in raw_words if w.lower() not in stops]
	no_stop_counts = Counter(no_stop_words)

	return raw_word_counts, no_stop_counts



if __name__ == '__main__':
    app.run()