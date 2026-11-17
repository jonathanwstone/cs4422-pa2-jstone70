import re
import string
from nltk.corpus import stopwords

stopWords = set(stopwords.words("english"))
edgeCharacters = string.punctuation + "\u2039\u203a\u2022"

def normalize_line(line):
    return " ".join(line.split())

def tokenize(text):

    text= text.lower()
    text = text.replace("\u2019", "'")
    text = text.replace("\u2018", "'")
    text = text.replace("\u201c", " ")
    text = text.replace("\u201d", " ")
    text = text.replace("\u2014", " ")
    text = text.replace("\u2013", " ")

    text = re.sub(r"(?<=[a-z])-(?=[a-z])", " ", text)
    tokens = text.split()
    result =[]
    for token in tokens:
        token = token.strip(edgeCharacters)
        if token == "" :
            continue
        if token in stopWords:
            continue
        result.append(token)
    return result
