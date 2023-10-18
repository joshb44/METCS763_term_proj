import os
import json
import random
import openai
from flask import Flask, redirect, render_template, request, url_for

from VacationPackages import VacationPackages

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

vacation_packages = VacationPackages()


@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        user_input = request.form["user_input"]

        sentiment_prompt = generate_sentiment_analysis_prompt(user_input)

        # Prompt ChatGPT to do sentiment analysis on the user's input
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user",
                       "content": sentiment_prompt}])

        parsed_sentiments = json.loads(response.choices[0].message['content'])

        filtered_packages = filter_packages_by_sentiments(parsed_sentiments)

        package = select_package(filtered_packages)

        pitch_prompt = generate_package_sales_pitch_prompt(package, parsed_sentiments,
                                   vacation_packages.tones)

        print(pitch_prompt, '\n')

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user",
                       "content": pitch_prompt}])
        return redirect(url_for("index", result=response.choices[0].message['content']))

    result = request.args.get("result")
    return render_template("index.html", result=result)





def generate_sentiment_analysis_prompt(user_input):
    """
    Construct a prompt for the OpenAI API to request that the AI model perform
    sentiment analysis on the user's input and determine the vacation style,
    environment, and travel companions that the user prefers. Prompt also
    specifies that we will want a JSON object as the response.

    :param user_input: The text input by the user.
    :return: The formatted text to be sent to OpenAI API.
    """
    return """Our travel agency’s application just asked a prospective customer
     to describe their ideal vacation. They responded as follows: 
     {user_input}
     Please use sentiment analysis to determine which following word best 
     describes the type of vacation the customer is seeking based on their 
     response: 
     Relaxing, Adventurous, Dining, Exploratory

    Repeat this process to determine which following word best describes the
    environment the customer prefers for their vacation: 
    Beach, Wilderness, Urban

    Repeat this process to determine which of the following best describes who 
    will be traveling with the customer:
    Alone, With Significant Other, With Family, With Friends
    
	Your response should be a JSON object in the following format:
	{{vacation_type: Type, environment: Type, companions: Type}}

	Do not make your response conversational, 
	include only the JSON object.""".format(user_input=user_input)


def filter_packages_by_sentiments(parsed_sentiments):
    """
    Uses our three 'Sentiments' (Vacation Type, Environment, and Companions) to
    filter our available packages down to those that meet the user's desires.

    :param parsed_sentiments: A dict of three sentiments
    :return: a dict of filtered packages
    """
    dests_filtered_by_type = \
        {key: values for key, values in vacation_packages.destinations.items()
         if parsed_sentiments['vacation_type'] in values}

    dests_filtered_by_env = \
        {key: values for key, values in dests_filtered_by_type.items()
         if parsed_sentiments['environment'] in values}

    # Note that if a sentiment finds no match, we want to revert to the previous
    # stage of filtration rather than abandoning all packages
    if not dests_filtered_by_env:
        dests_filtered_by_env = dests_filtered_by_type

    dests_filtered_by_comp = \
        {key: values for key, values in dests_filtered_by_env.items()
         if parsed_sentiments['companions'] in values}

    if not dests_filtered_by_comp:
        dests_filtered_by_comp = dests_filtered_by_env

    return dests_filtered_by_comp

def select_package(filtered_packages):
    """
    In the event that more than one package passes all sentiment filters, simply
    choose a random one.

    :param filtered_packages: A dict of all packages that passed the filters
    :return: a dict with a single package
    """
    random_package = dict([random.choice(list(filtered_packages.items()))])

    return random_package

def generate_package_sales_pitch_prompt(package, parsed_sentiments, tones):
    """
    Construct a prompt for the OpenAI API to request that the AI model craft a
    tailored response to the user which consists of a sales pitch for a locale
    with an appropriate tone and details all specified by the application.

    :param package: the selected package
    :param parsed_sentiments: the sentiments returned from the initial prompt
    :param tones: a dict of tones that match vacation types
    :return: The formatted text to be sent to OpenAI API.
    """
    locale = list(package.keys())[0]
    type = ""
    environment = ""
    companions = ""
    tone = ""

    if parsed_sentiments['vacation_type'] in list(package.values())[0]:
        type = parsed_sentiments['vacation_type']
        tone = tones[type]

    if parsed_sentiments['environment'] in list(package.values())[0]:
        environment = parsed_sentiments['environment']

    if parsed_sentiments['companions'] in list(package.values())[0]:
        companions = parsed_sentiments['companions']

    return """Pretend you are a travel agent making a first-time recommendation
     to a customer that they purchase a package to visit {locale}. Use a 
     positive {tone} tone and emphasize the qualities about {locale} that 
     make it a great {type} place. Emphasize the allure of its {environment} 
     setting as well as its appeal to those traveling {companions}. Confine your 
     response to a single paragraph. """.format(locale=locale, type=type,
                                                tone=tone,
                                                environment=environment,
                                                companions=companions)