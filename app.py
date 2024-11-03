from flask import Flask, render_template, request
from newsapi import NewsApiClient
import pycountry
import re  # Import regular expressions module

app = Flask(__name__)

# Initialize the News API client with your API key
newsapi = NewsApiClient(api_key="a7542233f91042b9abf1284667287828")

# Default country set to the United States
default_country = "United States"
countries = {country.name: country.alpha_2 for country in pycountry.countries}

# Available categories for news
available_categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

def clean_description(description):
    """Remove unwanted text and return a clean description."""
    if not description or not description.strip():
        return ""  # Return an empty string if no description
    
    # Use regex to remove any unwanted trailing characters like "+4561 chars"
    clean_desc = re.sub(r'\s*\+\d+\s*chars', '', description)

    return clean_desc

def truncate_description(description, word_limit=100):
    """Truncate the description to the specified word limit."""
    cleaned_desc = clean_description(description)
    
    words = cleaned_desc.split()
    if len(words) > word_limit:
        return " ".join(words[:word_limit])  # Keep only up to word_limit words
    return cleaned_desc

def fetch_latest_articles(limit=5):
    """Fetch the latest articles for the bulletin, excluding removed articles."""
    try:
        all_articles = newsapi.get_top_headlines(
            language='en',
            country='us',  # Default to US for the bulletin
        )
        if all_articles and all_articles.get("articles"):
            # Return only the specified number of latest articles
            return all_articles["articles"][:limit]  # Limit to 'limit' latest articles
    except Exception as e:
        print(f"Error fetching latest articles: {e}")
    return []  # Return an empty list if there's an error

@app.route("/", methods=["GET", "POST"])
def index():
    headlines = []
    bulletin_articles = fetch_latest_articles()  # Fetch latest articles for the bulletin
    error_message = None  # To capture error messages
    selected_country = default_country
    search_keywords = request.form.get("search", "").lower()  # Get search keywords from the form

    # Default to the selected category based on the POST request
    category = request.form.get("category", "").lower() if request.method == "POST" else available_categories[0]  

    if request.method == "POST":
        selected_country = request.form.get("country", default_country)

        # Use the country code based on the selected country
        country_code = countries.get(selected_country.title(), "US").lower()

        try:
            # Fetch news based on category or search keywords
            if search_keywords:
                # Split the search_keywords by commas or spaces to support multiple keywords
                keywords_list = [keyword.strip() for keyword in search_keywords.split(',') if keyword.strip()]
                search_query = " AND ".join(keywords_list)

                # Search for articles using the keywords while also considering the selected category
                all_articles = newsapi.get_everything(
                    q=search_query,
                    language="en",
                    sort_by="relevancy",
                )
                if all_articles and all_articles.get("articles"):
                    headlines = all_articles["articles"]
                else:
                    error_message = "No articles found for the provided keywords."
            else:
                # Fetch top headlines based on the selected category and country
                top_headlines = newsapi.get_top_headlines(
                    category=category,  # Use the selected category
                    language="en",
                    country=country_code,
                )
                if top_headlines and top_headlines.get("articles"):
                    headlines = top_headlines["articles"]
                else:
                    error_message = "No headlines found for the selected category."
        except Exception as e:
            error_message = f"An error occurred while fetching news: {e}"

    # Truncate descriptions for each article
    for article in headlines:
        article_content = article.get("content", "") or article.get("description", "")
        article["description"] = truncate_description(article_content)  # Truncate to 100 words

    return render_template(
        "index.html",
        headlines=headlines,
        bulletin_articles=bulletin_articles,  # Pass bulletin articles to the template
        error_message=error_message,
        countries=countries,
        selected_country=selected_country,
        available_categories=available_categories,
        selected_category=category,
        search_keywords=search_keywords,
    )

if __name__ == "__main__":
    app.run(debug=True)
