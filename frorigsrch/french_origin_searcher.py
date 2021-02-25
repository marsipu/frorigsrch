import re

from bs4 import BeautifulSoup
import urllib.request

# Pattern to find next link for multiple results
mr_pattern = r'<a href="(.*)">View full entry</a>'

test_words = ['degree', 'gratin']
test_patterns = [
    'Origin:.{,500}French',
    'Etymology:.{,500}French',
    'Etymons:.{,500}French'
]


def get_word_origin(search_url, word, search_patterns):
    # For avoid 403-error using User-Agent
    req = urllib.request.Request(search_url, headers={'User-Agent': "Magic Browser"})
    response = urllib.request.urlopen(req)
    html = response.read()
    # Parsing response
    soup = BeautifulSoup(html, 'html.parser')
    translation = origin_type = None

    if soup.title.text == 'Home : Oxford English Dictionary':
        raise RuntimeError('You seem to have no access to Oxford English Dictionary (check VPN)')
    if soup.title.text == 'Quick search results : Oxford English Dictionary':
        fe_match = re.search(mr_pattern, str(soup.body))
        if fe_match:
            newsearch_html = 'https://www.oed.com' + fe_match.group(1)
            translation, origin_type = get_word_origin(newsearch_html, word, search_patterns)
    elif soup.title.text == 'No Search Results : Oxford English Dictionary':
        translation = origin_type = 'Not found'
    else:
        body_string = soup.body.text
        for search_pattern in search_patterns:
            # Get first occurrence which matches the patterns
            match = re.search(fr'{search_pattern}', body_string)
            if match:
                print(f'French origin was found for {word}')
                translation = soup.title.text
                translation = translation.replace(': Oxford English Dictionary', '')
                origin_type = match.group()
                # Make output prettier
                while '  ' in origin_type:
                    origin_type = origin_type.replace('  ', '')
                origin_type = origin_type.replace('\xa0', '')

    return translation, origin_type


if __name__ == '__main__':
    for word in test_words:
        search_url = f'https://www.oed.com/search?searchType=dictionary&q={word}&_searchBtn=Search'
        result = get_word_origin(search_url, word, test_patterns)
        print(result)
