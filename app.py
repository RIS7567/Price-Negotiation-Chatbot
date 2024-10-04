import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

load_dotenv()

# Flask application setup
app = Flask(__name__)

CORS(app)

# NegotiationBot class handling both negotiation and sentiment analysis
class NegotiationBot:
    def __init__(self, api_key):
        self.client = None
        self.api_key = api_key
        self.init_openai_client()
        print("[DEBUG] NegotiationBot initialized.")
    
    def init_openai_client(self):
        try:
            self.client = openai  # Initialize OpenAI client
            openai.api_key = self.api_key
            print("[DEBUG] OpenAI client initialized.")
        except Exception as e:
            print(f"[ERROR] Error while initializing OpenAI client: {e}")

    # Step 1: Sentiment and politeness analysis using ChatCompletion
    def sentiment_and_politeness_analysis(self, user_message):
        messages = [
            {"role": "system", "content": "You are an assistant that analyzes the tone of user messages."},
            {"role": "user", "content": f"Analyze the following message for sentiment and politeness: '{user_message}'."},
            {"role": "user", "content": "Is the message polite or rude? Is the sentiment positive, neutral, or negative? Please respond with keywords such as 'polite', 'rude', 'positive', 'negative'."}
        ]
        
        try:
            print("[DEBUG] Sending sentiment and politeness analysis request to OpenAI.")
            completion = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4 or any other OpenAI model
                messages=messages,
                max_tokens=50,
                temperature=0.7
            )
            
            analysis_response = completion.choices[0].message.content.strip()
            print(f"[DEBUG] OpenAI sentiment and politeness analysis response: {analysis_response}")

            # Extract sentiment and politeness from the response
            polite = "polite" in analysis_response.lower()
            rude = "rude" in analysis_response.lower()
            
            if "positive" in analysis_response.lower():
                sentiment = "positive"
            elif "negative" in analysis_response.lower():
                sentiment = "negative"
            else:
                sentiment = "neutral"

            politeness = "polite" if polite else ("rude" if rude else "neutral")
            return sentiment, politeness

        except Exception as e:
            print(f"[ERROR] Error while performing sentiment and politeness analysis: {e}")
            return "Error", "neutral"

    # Step 2: Final negotiation based on sentiment and politeness using ChatCompletion
    def generate_negotiation_response(self, user_input, product_price, min_price, max_price, sentiment, politeness):
        # Adjust price based on sentiment and politeness
        price_adjustment = 0

        if politeness == "polite":
            if sentiment == "positive":
                price_adjustment = -10  # Offer a better deal for polite and positive sentiment
            elif sentiment == "negative":
                price_adjustment = -5  # Offer a small discount for politeness and negative sentiment
            else:
                price_adjustment = -3  # Slight discount for polite and neutral sentiment
        elif politeness == "rude":
            if sentiment == "negative":
                price_adjustment = 5  # Increase the price for rude and negative sentiment
            else:
                price_adjustment = 0  # No change for rude but positive/neutral sentiment

        adjusted_price = product_price + price_adjustment
        adjusted_price = max(min(adjusted_price, max_price), min_price)

        # Build conversation context for negotiation based on sentiment and politeness
        negotiation_messages = [
            {"role": "system", "content": "You are a negotiation bot for product pricing. Negotiate based on the user's sentiment and politeness."},
            {"role": "user", "content": f"The customer offered {user_input} for the product priced at {product_price}."},
            {"role": "system", "content": f"The product's price range is between {min_price} and {max_price}. The current adjusted price based on sentiment and politeness is {adjusted_price}."}
        ]

        try:
            print("[DEBUG] Sending negotiation request to OpenAI based on sentiment and politeness.")
            completion = self.client.chat.completions.create(
                model="gpt-4",  # Use GPT-4 or any other OpenAI model
                messages=negotiation_messages,
                max_tokens=150,
                temperature=0.7
            )

            final_response = completion.choices[0].message.content.strip()
            print(f"[DEBUG] Final negotiation bot response: {final_response}")
            return final_response

        except Exception as e:
            print(f"[ERROR] Error while generating negotiation response: {e}")
            return "Error in negotiation process."


# Initialize the NegotiationBot with API key
api_key = os.getenv("OPENAI_API_KEY")  # Alternatively, you can set your API key directly here
bot = NegotiationBot(api_key)

# Flask route for negotiation and sentiment analysis
@app.route('/negotiate', methods=['POST'])
def negotiate():
    try:
        data = request.json  # Read the JSON request body
        user_price = float(data['user_price'])
        min_price = float(data['min_price'])
        max_price = float(data['max_price'])
        initial_price = float(data['initial_price'])
        user_message = data.get('user_message', '')

        # Step 1: Perform sentiment and politeness analysis
        sentiment, politeness = bot.sentiment_and_politeness_analysis(user_message)

        # Step 2: Generate final negotiation response based on analysis
        bot_response = bot.generate_negotiation_response(user_price, initial_price, min_price, max_price, sentiment, politeness)
        
        return jsonify({
            "sentiment": sentiment,
            "politeness": politeness,
            "bot_response": bot_response
        })
    except Exception as e:
        print(f"[ERROR] Error while processing negotiation: {e}")
        return jsonify({"error": str(e)})


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000)
