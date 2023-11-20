import os
from dotenv import load_dotenv
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import json
from io import BytesIO
import time
import logging
import urllib.parse
from telegram.ext import MessageHandler, Filters

class MemeBot:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.TOKEN = "YOUR_TOKEN"
        self.USERNAME = "YOUR_USERNAME"
        self.GROUP_CHAT_ID = "YOUR_GROUP_CHAT_ID"
        # File to store user subscriptions
        self.SUBSCRIPTION_JSON_FILE = 'subscriptions.json'
        # Configure logging for error handling
        logging.basicConfig(filename='meme_bot.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

    # Function to get the total subscriber count
    def get_subscriber_count(self):
        try:
            with open(self.SUBSCRIPTION_JSON_FILE, 'r') as file:
                subscribed_users = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            subscribed_users = []

        return sum(user["subscribed"] for user in subscribed_users)

    # Function to send a message to the group chat
    def send_to_group(self, message):
        try:
            requests.post(f'https://api.telegram.org/bot{self.TOKEN}/sendMessage', json={
                'chat_id': self.GROUP_CHAT_ID,
                'text': message,
                'disable_notification': True,
            })
        except Exception as e:
            print(f"Failed to send message to group: {str(e)}")

    # Function to check if a user is subscribed
    def is_subscribed(self, user_id):
        try:
            with open(self.SUBSCRIPTION_JSON_FILE, 'r') as file:
                subscribed_users = json.load(file)

            user = next((user for user in subscribed_users if user["user_id"] == str(user_id)), None)
            return user and user["subscribed"]
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    # Function to subscribe a user
    def subscribe_user(self, user_id, username, first_name, last_name):
        try:
            with open(self.SUBSCRIPTION_JSON_FILE, 'r') as file:
                subscribed_users = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            subscribed_users = []

        existing_user = next((user for user in subscribed_users if user["user_id"] == str(user_id)), None)

        if not existing_user or not existing_user.get("subscribed", False):
            count = 0
            greet = "New subscriber!"
            name = first_name

            if existing_user:
                # Update existing user's subscription status
                existing_user["subscribed"] = True
                existing_user["meme_count"] = existing_user.get("meme_count", 0)  # Ensure meme_count exists
                count = existing_user["meme_count"]
            else:
            # Create a new user entry if the user doesn't exist
                new_user = {
                    "user_id": str(user_id),
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "subscribed": True,
                    "meme_count": 0,
                }
                subscribed_users.append(new_user)

            # Save the updated user data to the file
            with open(self.SUBSCRIPTION_JSON_FILE, 'w') as file:
                json.dump(subscribed_users, file)

            # Notify the group about the new or existing user's subscription
            group_message = f"🎉 {greet}\n\nUser ID: {user_id}\nUsername: @{username}\nFirst Name: {name}\nLast Name: {last_name}\nMeme Count: {count}\n\nTotal Subscribers: {self.get_subscriber_count()} 🚀"

            self.send_to_group(group_message)
        else:
            # If the user is already subscribed, send a welcome back message
            update.message.reply_text(f"🎉 Welcome back, {name}! You're already subscribed. Enjoy the memes and let the laughter continue! 😄")

    # Function to unsubscribe a user
    def unsubscribe_user(self, user_id):
        try:
            with open(self.SUBSCRIPTION_JSON_FILE, 'r') as file:
                subscribed_users = json.load(file)

            user = next((user for user in subscribed_users if user["user_id"] == str(user_id)), None)

            if user:
                # Update user's subscription status to unsubscribe
                user["subscribed"] = False

                # Notify the group about the user's unsubscription
                group_message = f"😢 User unsubscribed!\n\nUser ID: {user['user_id']}\nUsername: @{user['username']}\nFirst Name: {user['first_name']}\nLast Name: {user['last_name']}\nMeme Count: {user['meme_count']}\n\nTotal Subscribers: {self.get_subscriber_count() - 1} 📉"
                self.send_to_group(group_message)

            # Save the updated user data to the file
            with open(self.SUBSCRIPTION_JSON_FILE, 'w') as file:
                json.dump(subscribed_users, file)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    # Function to handle the /subscribe command
    def subscribe(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id
        username = update.message.from_user.username
        first_name = update.message.from_user.first_name
        last_name = update.message.from_user.last_name if update.message.from_user.last_name else ""
        try:
            with open(self.SUBSCRIPTION_JSON_FILE, 'r') as file:
                subscribed_users = json.load(file)

            existing_user = next((user for user in subscribed_users if user["user_id"] == str(user_id)), None)

            if existing_user and existing_user["subscribed"]:
                # If the user is already subscribed, send a welcome back message
                update.message.reply_text(f"🎉 Welcome back, {first_name}! You're already part of the MemeSpotBot family. Enjoy unlimited memes and keep the laughter rolling! 😄")

            else:
                # Subscribe the user if not already subscribed
                self.subscribe_user(user_id, username, first_name, last_name)
                update.message.reply_text("🎉 Congratulations! You're now part of the MemeSpotBot family. Get ready for unlimited memes and lots of laughter! 😄")
        except Exception as e:
            # Handle errors gracefully
            self.handle_error(update, e)

    # Function to handle the /unsubscribe command
    def unsubscribe(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id
        try:
            with open(self.SUBSCRIPTION_JSON_FILE, 'r') as file:
                subscribed_users = json.load(file)

            user = next((user for user in subscribed_users if user["user_id"] == str(user_id)), None)

            if user and user["subscribed"]:
                # Unsubscribe the user if already subscribed
                self.unsubscribe_user(user_id)
                update.message.reply_text(f'😢 You\'ve been unsubscribed, {user["first_name"]}. To resubscribe and get more memes, use /subscribe. 😔')
            else:
                # If the user is not subscribed, or already unsubscribed, inform them
                update.message.reply_text('🤷‍♂️ You haven\'t subscribed yet or already unsubscribed. To subscribe and enjoy unlimited memes, use /subscribe. 😊')
        except Exception as e:
            # Handle errors gracefully
            self.handle_error(update, e)

    # Function to handle the /start command
    def start(self, update: Update, context: CallbackContext) -> None:
        try:
            user_id = update.message.from_user.id
            with open(self.SUBSCRIPTION_JSON_FILE, 'r') as file:
                subscribed_users = json.load(file)

            user = next((user for user in subscribed_users if user["user_id"] == str(user_id)), None)

            if user and user["subscribed"]:
                # If the user is already subscribed, send a welcome back message
                update.message.reply_text(f"👋 Welcome back, {user['first_name']}! It's great to have you here again! 😄 Ready for some laughter? Explore the features and enjoy a dose of humor! 🚀🤣")
            else:
                # If the user is not subscribed, send a welcome message
                update.message.reply_text("🎉 Welcome to MemeSpotBot! 🌟 We're excited to have you on board! 😄 Get ready for a meme-tastic experience! Explore the features and let the laughter begin! 🚀🤣")
        except Exception as e:
            # Handle errors gracefully
            self.handle_error(update, e)

    # Function to handle errors and send an error message
    def handle_error(self, update: Update, error: Exception) -> None:
        try:
            error_message = f"🛑 Oops! Something went wrong:\n{str(error)}\n\nApologies for the inconvenience. Please try again later!"
            update.message.reply_text(error_message)
        except Exception as e:
            print(f"Error handling failed: {str(e)}")

    # Error handler function for the bot
    def error_handler(self, update, context):
        try:
            error_message = f'Update "{update}" caused error "{context.error}"'
            logging.error(error_message)
            print(error_message)
            update.message.reply_text(f"🛑 Sorry, something went wrong: {context.error}\nPlease try again later.")
        except Exception as e:
            print(f"Error handling failed: {str(e)}")

    # Function to handle the /feedback command
    def feedback(self, update: Update, context: CallbackContext) -> None:
        try:
            # Example feedback to guide users
            example_feedback = "Example: /feedback I love the memes! They always brighten my day. Keep up the good work."
            # Extract user's feedback from the command
            user_feedback = update.message.text.replace('/feedback', '').strip()

            if user_feedback:
                # Format and encode the feedback for a clickable link
                formatted_feedback = f'Your feedback: `{user_feedback}`'
                encoded_feedback = urllib.parse.quote(formatted_feedback, safe='')
                feedback_link = f"📣 [Send Feedback](https://t.me/{self.USERNAME}?text={encoded_feedback})"
                feedback_message = f"Thank you for your feedback! \n{formatted_feedback}\n\n{feedback_link}"
                update.message.reply_text(feedback_message, parse_mode=ParseMode.MARKDOWN)
            else:
                # If no feedback is provided, inform the user
                update.message.reply_text(f'🤔 Please provide your feedback along with the /feedback command. {example_feedback}', parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            # Handle errors gracefully
            self.handle_error(update, e)

    # Function to display the bot's help message
    def help_command(self, update: Update, context: CallbackContext) -> None:
        help_text = """
🌟 Welcome to MemeSpotBot! 🌟

Explore these fun commands:

- /start: Begin your meme adventure
- /meme: Grab a random meme for a good laugh
- /subscribe: Join us for unlimited memes
- /unsubscribe: Take a break from memes
- /feedback [your feedback]: Share your thoughts
- /privacy: Learn how we handle your data
- /help: See this message again

Enjoy the laughter! 😄🚀
"""
        update.message.reply_text(help_text)

    # Function to increment the meme count for a user
    def increment_meme_count(self, user_id):
        try:
            with open(self.SUBSCRIPTION_JSON_FILE, 'r') as file:
                subscribed_users = json.load(file)

            user = next((user for user in subscribed_users if user["user_id"] == str(user_id)), None)

            if user:
                # Increment the user's meme count and notify the group for milestones
                user["meme_count"] = user["meme_count"] + 1
                if user["meme_count"] % 100 == 0:
                    group_message = f"🎉 Subscriber's alert!\n\nUser ID: {user['user_id']}\nUsername: @{user['username']}\nFirst Name: {user['first_name']}\nLast Name: {user['last_name']}\nMeme Count: {user['meme_count']}\n\nTotal Subscribers: {self.get_subscriber_count()} 🚀"
                    self.send_to_group(group_message)
                # Save the updated meme count to the file
                with open(self.SUBSCRIPTION_JSON_FILE, 'w') as file:
                    json.dump(subscribed_users, file)

        except (FileNotFoundError, json.JSONDecodeError):
            pass

    # Function to handle the /meme command and send a random meme
    def meme(self, update: Update, context: CallbackContext) -> None:
        try:
            user_id = update.message.from_user.id
            if self.is_subscribed(user_id):
                meme_api_url = 'YOUR_MEME_API'
                max_retries = 3

                for _ in range(max_retries):
                    try:
                        # Request a random meme from the meme API
                        response = requests.get(meme_api_url)
                        response.raise_for_status()

                        meme_data = response.json()
                        meme_url = meme_data.get('url')
                        meme_caption = meme_data.get('title', 'Enjoy this meme!')

                        if meme_url:
                            is_gif = meme_url.endswith('.gif')
                            media_response = requests.get(meme_url)
                            media_bytes = BytesIO(media_response.content)

                            if is_gif:
                                # Send a GIF if the meme is a GIF
                                update.message.reply_document(media_bytes, caption=f'😄 {meme_caption}')
                            else:
                                # Send a photo if the meme is an image
                                update.message.reply_photo(media_bytes, caption=f'😄 {meme_caption}')

                            # Increment meme count using the new function
                            self.increment_meme_count(user_id)

                            return
                        else:
                            # If meme media retrieval fails, inform the user
                            update.message.reply_text('❌ Failed to fetch meme media. Please try again later.')
                            return
                    except requests.RequestException as e:
                        # Handle request errors and retry
                        update.message.reply_text(f'🚫 Request failed: {e}')
                        time.sleep(2)
                    except KeyError as e:
                        # Handle malformed API response
                        update.message.reply_text(f'🤖 Malformed response from the API. Please try again later.')
                        return
                    except Exception as e:
                        # Handle other errors
                        update.message.reply_text(f'🛑 An error occurred: {e}')
                        return

                # If meme retrieval fails after multiple attempts, inform the user
                update.message.reply_text('❌ Failed to fetch memes after multiple attempts. Please try again later.')
            else:
                # If the user is not subscribed, prompt them to subscribe
                update.message.reply_text("🚀 Ready for some laughter? To access unlimited memes, simply use /subscribe and join the meme-tastic fun! 😄")

        except Exception as e:
            # Handle errors gracefully
            self.handle_error(update, e)

    # Function to handle unknown commands and provide guidance
    def unknown(self, update, context):
        update.message.reply_text("Oopsie! 🙊 I didn't catch that command. 🤔 If you need help or want to explore what I can do, simply type /help. Enjoy the memes! 🚀😄")

    # Function to display the bot's privacy message
    def privacy(self, update: Update, context: CallbackContext) -> None:
        privacy_message = """🛡 **Your Privacy Matters!**

We want you to know how we handle your data:

- 📊 **Data We Collect:** Only the essentials - your user ID, username, and subscription status.

- 🤖 **Why We Need It:** We use this info to give you memes and manage your subscriptions - that's it!

- 🙅‍♂️ **No Sharing:** Your data is YOURS. We don't share it with anyone else.

🤔 **Got Questions or Concerns?**
        We're here! Use /feedback to reach out with any questions or concerns about your data.

🚀 **Enjoy MemeSpotBot!**
Thanks for being part of the fun!
        """
        update.message.reply_text(privacy_message, parse_mode=ParseMode.MARKDOWN)

    # Main function to start the bot and handle user interactions
    def main(self) -> None:
        try:
            # Create the subscriptions file if it doesn't exist
            if not os.path.exists(self.SUBSCRIPTION_JSON_FILE):
                with open(self.SUBSCRIPTION_JSON_FILE, 'w') as file:
                    json.dump([], file)

            # Set up the Telegram bot using the python-telegram-bot library
            updater = Updater(token=self.TOKEN, use_context=True)
            dp = updater.dispatcher

            # Add command and message handlers
            dp.add_handler(CommandHandler("start", self.start))
            dp.add_handler(CommandHandler("meme", self.meme))
            dp.add_handler(CommandHandler("subscribe", self.subscribe))
            dp.add_handler(CommandHandler("feedback", self.feedback))
            dp.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
            dp.add_handler(CommandHandler("help", self.help_command))
            dp.add_handler(CommandHandler("privacy", self.privacy))
            dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.unknown))

            # Add error handler
            dp.add_error_handler(self.error_handler)

            # Start polling for updates
            updater.start_polling()

            # Keep the bot running until interrupted
            updater.idle()
        except Exception as e:
            # Handle errors in the main function
            print(f"An error occurred in the main function: {str(e)}")

if __name__ == '__main__':
    # Create an instance of the MemeBot class and start the bot
    bot = MemeBot()
    bot.main()