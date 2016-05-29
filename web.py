from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
import os
import sys
import requests
import operator
import re
import nltk
from collections import Counter
from bs4 import BeautifulSoup
import stop_words


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import Result


@app.route('/', methods=['GET','POST'])
def index():
	errors = []
	results = {}
	r = None  # prevents uninitialization error, which happens on Heroku but not my laptop
	if request.method == 'POST':
		# get the URL entered
		try:
			url = request.form['url']
			r = requests.get(url)
		except:
			errors.append("Unable to get URL - try again")

	if r is not None:
		(raw_counts, stop_removed_count) = count_words_from_html(r)

		# package results for web display
		results = sorted(stop_removed_count.items(), key=operator.itemgetter(1), reverse=True)[:10]

		# store results in the database
		try:
			db_result = Result(
				url=url,
				result_all=raw_counts,
				result_no_stop_words=stop_removed_count
				)
			db.session.add(db_result)
			db.session.commit()
		except Exception as e:
			err = "Unable to add results to the database: %s" % e
			errors.append(err)

	return render_template('index.html', errors=errors, results=results)

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