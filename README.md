# LinkedInfluencer 🚀

Welcome to **LinkedInfluencer**, a cutting-edge Python application designed to transform your LinkedIn presence by automating the creation and posting of engaging content. Leveraging the power of RSS feeds, OpenAI's GPT, and AWS services, this tool ensures your LinkedIn feed remains active, relevant, and irresistibly engaging—all without lifting a finger!

---

## Table of Contents

- [✨ Features](#-features)
- [🔧 Architecture](#-architecture)
- [🚀 Getting Started](#-getting-started)
    - [📦 Prerequisites](#-prerequisites)
    - [🔨 Installation](#-installation)
- [🛠 Configuration](#-configuration)
- [💻 Usage](#-usage)

---

## ✨ Features

- **Automated RSS Aggregation**: Fetches and aggregates news from TechCrunch and Ars Technica. Can easily be updated to use different sources.
- **AI-Powered Content Creation**: Utilizes OpenAI to generate compelling LinkedIn posts.
- **Cloud-Native Deployment**: Fully automated using AWS Lambda, DynamoDB, and S3.
- **Automatic Posting**: Automatically posts content to LinkedIn using Zapier.
- **Scalable and Maintainable**: Containerized with Docker for easy scalability and maintenance.

---

## 🔧 Architecture

![Architecture Diagram](path/to/architecture-diagram.png)

## 🚀 Getting Started

### 📦 Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python 3.11+**: Ensure Python is installed on your machine.
- **Docker**: For containerizing the application.
- **AWS Account**: To deploy AWS Lambda, DynamoDB, and S3 services.
- **OpenAI API Key**: To utilize OpenAI's GPT for content creation.
- **Zapier Account**: For automatically posting content to LinkedIn.
- **LinkedIn Account**: Well, duh.

### 🔨 Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/linkedinfluencer-automator.git
   cd linkedinfluencer-automator
   ```

2. **Set Up Environment Variables**

   Create a `.env` file based on the provided template:

   ```bash
   cp .env.template .env
   ```

   Fill in the required environment variables in `.env`:

   ```env
   OPENAI_API_KEY=YOUR_OPENAI_API_KEY
   AWS_REGION=YOUR_AWS_REGION
   DYNAMODB_SCRAPED_TABLE_NAME=YOUR_DYNAMODB_SCRAPED_TABLE_NAME
   DYNAMODB_POSTS_TABLE_NAME=YOUR_DYNAMODB_POSTS_TABLE_NAME
   S3_BUCKET_NAME=YOUR_S3_BUCKET_NAME
   RSS_FEED_KEY=YOUR_RSS_FEED_S3_KEY
   RSS_FEED_TITLE=YOUR_RSS_FEED_TITLE
   RSS_FEED_DESCRIPTION=YOUR_RSS_FEED_DESCRIPTION
   RSS_FEED_LINK=YOUR_RSS_FEED_LINK
   ```

3. **Install Dependencies**

   It's recommended to use a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

## 💻 Usage

The application can be run locally or deployed to AWS Lambda. Below are instructions for both scenarios.

### 📌 Running Locally

1. **Activate Virtual Environment**

   ```bash
   source venv/bin/activate
   ```

2. **Execute the Script**

   ```bash
   python main.py aggregate_news
   python main.py process_items
   ```

   Available actions:

    - `aggregate_news`: Fetches RSS feeds and saves items to DynamoDB.
    - `process_items`: Processes saved DynamoDB items to create LinkedIn posts and trigger posting.
   These can also be set via an environment variable "ACTION". The default value is "aggregate_news".

### 🌩 Deploying to AWS Lambda

1. **Build Docker Image**

   Ensure you're using the correct platform (`x86` or `arm`):

   ```bash
   docker build -t linkedinfluencer .
   ```

2. **Tag the Docker Image**

   Replace `<AWS_ACCOUNT_ID>` and `<REGION>` with your AWS details:

   ```bash
   docker tag linkedinfluencer:latest <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/linkedinfluencer:latest
   ```

3. **Push to Amazon ECR**

   ```bash
   docker push <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/linkedinfluencer:latest
   ```

4. **Set Up AWS Lambda**

    - **Create a Lambda Function** using the pushed Docker image.
    - **Set Environment Variable "ACTION"**: Decide on "aggregate_news" or "process_items" depending on the Lambda function.
    - **Assign Execution Role**: Ensure the Lambda execution role has permissions to access S3, DynamoDB, and other required AWS services.

5. **Schedule with EventBridge**

    - **Data Gathering**: Trigger `aggregate_news` at 00:00 daily.
    - **Post Creation**: Trigger `process_items` during peak LinkedIn engagement times.

---

## 🔗 Integration

**Zapier** is integrated to handle the automated posting process:

1. **RSS Feed Setup**: The application updates an XML RSS feed stored in S3.
2. **Zapier Connection**: Configure Zapier to monitor the RSS feed and post new items to LinkedIn.
3. **Automation Workflow**: As new posts are added to the RSS feed, Zapier triggers LinkedIn posts automatically.

## 🛠️ Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.
