import openai
import os
from dotenv import load_dotenv
from textblob import TextBlob
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

    # Function to perform sentiment analysis using TextBlob
    def sentiment_analysis(self, user_message):
        try:
            print("[DEBUG] Performing sentiment analysis using TextBlob.")
            blob = TextBlob(user_message)
            polarity = blob.sentiment.polarity  # Get polarity score (-1 to 1)

            # Determine sentiment based on polarity score
            if polarity > 0:
                sentiment = "positive"
            elif polarity < 0:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            print(f"[DEBUG] Sentiment analysis result: {sentiment}")
            return sentiment

        except Exception as e:
            print(f"[ERROR] Error while performing sentiment analysis: {e}")
            return "Error in sentiment analysis."

    # Function to generate negotiation response influenced by sentiment
    def generate_negotiation_response(self, user_input, product_price, min_price, max_price, sentiment):
        # Adjust price based on sentiment
        price_adjustment = 0

        if sentiment == "positive":
            price_adjustment = -5  # Offer a discount for positive sentiment
        elif sentiment == "negative":
            price_adjustment = 5  # Be more defensive for negative sentiment

        adjusted_price = product_price + price_adjustment
        # Ensure the adjusted price is within the min and max bounds
        adjusted_price = max(min(adjusted_price, max_price), min_price)

        # Build conversation context based on user input and adjusted pricing details
        messages = [
            {"role": "system", "content": "You are a negotiation bot for product pricing."},
            {"role": "user", "content": f"The customer offered {user_input} for the product priced at {product_price}."},
            {"role": "system", "content": f"The product's price range is between {min_price} and {max_price}. Based on sentiment, the bot's current price is {adjusted_price}."}
        ]

        # Send request to OpenAI API through the client
        try:
            print("[DEBUG] Sending negotiation context to OpenAI API through client:", messages)
            completion = self.client.chat.completions.create(
                model="gpt-4o",  # Use the appropriate model
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )

            output = completion.choices[0].message.content.strip()
            print(f"[DEBUG] Negotiation bot response: {output}")
            return output

        except Exception as e:
            print(f"[ERROR] Error while generating negotiation response: {e}")
            return "Error in negotiation process."


# Initialize the NegotiationBot with API key
api_key = os.getenv("OPENAI_API_KEY")  # Alternatively, you can set your API key directly here
bot = NegotiationBot(api_key)

# Flask route for negotiation and sentiment analysis, designed for testing with Postman
@app.route('/negotiate', methods=['POST'])
def negotiate():
    try:
        data = request.json  # Read the JSON request body
        user_price = float(data['user_price'])
        min_price = float(data['min_price'])
        max_price = float(data['max_price'])
        initial_price = float(data['initial_price'])
        user_message = data.get('user_message', '')

        # Perform sentiment analysis if the user provided a message
        sentiment = None
        if user_message:
            sentiment = bot.sentiment_analysis(user_message)

        # Get the negotiation response influenced by sentiment
        bot_response = bot.generate_negotiation_response(user_price, initial_price, min_price, max_price, sentiment)
        
        return jsonify({
            "sentiment": sentiment,
            "bot_response": bot_response
        })
    except Exception as e:
        print(f"[ERROR] Error while processing negotiation: {e}")
        return jsonify({"error": str(e)})


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000)
