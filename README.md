# **🏆 AI Slack Chatbot with Hugging Face Integration**

This is a **Slack chatbot** that responds to mentions using **Hugging Face's Mistral-7B-Instruct-v0.3** model.  
Built with **Flask, Slack Bolt, and Hugging Face API**.

---

## **🚀 Features**
✅ Listens for `@mentions` in Slack.  
✅ Uses **Hugging Face API** to generate responses.  
✅ Maintains conversation history for contextual replies.  
✅ Runs on **Flask** and is **deployed on Render** you may AWS, or any server.  

---

## **📂 Project Structure**
📁 Slack-Chatbot_Droid/

│── 📄 app.py => Main Flask application

│── 📄 .env => Environment variables (not included in GitHub)

│── 📄 requirements.txt => Python dependencies

│── 📄 README.md => Project documentation


---

## **🛠️ Setup & Installation**

### **1️⃣ Clone the Repository**
```
git clone https://github.com/SenArnab/Slack-Chatbot_Droid.git
cd Slack-Chatbot_Droid
```
---
### **2️⃣ Install Dependencies**
```
pip install -r requirements.txt
```
### **3️⃣ Set Up Environment Variables**
Create a .env file in the project root and add:
```
SLACK_BOT_TOKEN=xoxb-XXXXXXXXXXXX
SLACK_SIGNING_SECRET=XXXXXXXXXXXX
HUGGINGFACE_API_KEY=hf_XXXXXXXXXXXXXXXXXXXXXXXX
PORT=3000
```
📌 Replace XXXXXXXXX with your actual Slack and Hugging Face credentials.


## **🚀 Running the Bot**
Start the bot with:
```
python app.py
```
## **🔗 Deploying the Bot on Render**
* Push your code to GitHub
```
git add .
git commit -m "Initial commit"
git push origin main
```
* Go to Render and create a new Web Service.

* Connect your GitHub repository.

* Set up environment variables (`SLACK_BOT_TOKEN, HUGGINGFACE_API_KEY, etc.`).

* Deploy and start the service! 🚀

## **📌 How to Use in Slack**
* Invite the bot to a channel like:
```
/invite @Arnab's Droid
```
* Mention the bot in Slack like:
```
@Arnab's Droid, What is a Tiger?

```
* The bot will generate a response using Hugging Face AI.

## **📜 License**
This project is MIT licensed. Feel free to modify and improve it!





## **📌Use My app**
* To use my app mail me at senarnab414@gmail.com, and I will share you an invite link to my slack workspace wherein you will be able to check out the chatbot.


## **👨‍💻Authors**
* Made with ❤️ by [@SenArnab](https://github.com/SenArnab)

