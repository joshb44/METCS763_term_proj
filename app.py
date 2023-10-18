import os
import json
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

        # Prompt ChatGPT to do sentiment analysis on the user's input
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user",
                       "content": sentiment_analysis_prompt(user_input)}])

        parsed_sentiments = json.loads(response.choices[0].message['content'])

        print(parsed_sentiments['vacation_type'] + parsed_sentiments['environment'] + parsed_sentiments['companions'] + '\n')

        filtered_packages = filter_packages_by_sentiments(parsed_sentiments)

        print(filtered_packages.keys())

        # response = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo",
        #     messages=[{"role": "user",
        #                "content": sentiment_analysis_prompt(user_input)}])
        # return redirect(url_for("index", result=response.choices[0].message['content']))

    result = request.args.get("result")
    return render_template("index.html", result=result)





def sentiment_analysis_prompt(user_input):
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
     Relaxing, Adventurous, Culinary, Isolated, Exploratory

    Repeat this process to determine what environment the customer prefers for 
    their vacation: 
    Beach, Wilderness, Urban

    Repeat this process to determine who will be traveling with the customer:
    Alone, With Significant Other, With Family, With Friends
	Your response should be a JSON object in the following format:
	{{vacation_type: Type, environment: Type, companions: Type}}

	Do not make your response conversational, 
	include only the JSON object.""".format(user_input=user_input)


def filter_packages_by_sentiments(parsed_sentiments):
    dests_filtered_by_type = \
        {key: values for key, values in vacation_packages.destinations.items()
         if parsed_sentiments['vacation_type'] in values}

    dests_filtered_by_env = \
        {key: values for key, values in dests_filtered_by_type.items()
         if parsed_sentiments['environment'] in values}

    if not dests_filtered_by_env:
        dests_filtered_by_env = dests_filtered_by_type

    dests_filtered_by_comp = \
        {key: values for key, values in dests_filtered_by_env.items()
         if parsed_sentiments['companions'] in values}

    if not dests_filtered_by_comp:
        dests_filtered_by_comp = dests_filtered_by_env

    return dests_filtered_by_comp
