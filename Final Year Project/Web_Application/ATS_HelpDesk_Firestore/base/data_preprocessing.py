import pandas as pd
import numpy as np
import re
import contractions
import nltk

from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

description = ''
     
def apply_contractions(text):
    new_phrase = []
    for word in text.split():
        new_phrase.append(contractions.fix(word))
        
    return ' '.join(new_phrase)


stop_words = set(stopwords.words('english'))

def text_cleaner(text):
    #converting to lowercase
    newString = text.lower()
    #removing links
    newString = re.sub(r'(https|http)?:\/\/(\w|\.|\/|\?|\=|\&|\%)*\b', '', newString) 
    #fetching alphabetic characters
    newString = re.sub("[^a-zA-Z]", " ", newString)
    #removing stop words
    tokens = [w for w in newString.split() if not w in stop_words] 
    long_words=[]
    for i in tokens:
        #removing short words
        if len(i)>1:                                                 
            long_words.append(i)   
    return (" ".join(long_words)).strip()


# function to genarate word tokens for tokenizers
def tokenization_func(text):
        return word_tokenize(text)

# Lemmatization
# Map POS tags to wordnet tags
# This step is necessary because the lemmatizer requires WordNet tags instead of POS tags
wordnet_tags = {'N': wordnet.NOUN, 'V': wordnet.VERB, 'R': wordnet.ADV, 'J': wordnet.ADJ}

lemmatizer = WordNetLemmatizer()

# Normalize the words using lemmatization with the appropriate POS tags

def lemmatization(list_part_of_speech_tagging):
     
     list_of_lemmatized_sen = []
     lemmas = []
     for word, pos in list_part_of_speech_tagging:
         if pos[0] in wordnet_tags:
             tag = wordnet_tags[pos[0]]
             lemma = lemmatizer.lemmatize(word, tag)
             lemmas.append(lemma)
         else:
             lemmas.append(word)
     # Join the lemmas back into a normalized sentence
     normalized_sentence = " ".join(lemmas)
     # insert the lemmatized(normalized_sentence) sentence in a new list called list_of_lemmatized_sen
     list_of_lemmatized_sen.append(normalized_sentence)
     
     return list_of_lemmatized_sen


list_of_sen_with_part_of_speech_tagging = []
tokenize_list = []
list_of_words = []
description = ""
def pre_process_data(text):
     print("Original text is: ", text)
     description = apply_contractions(text)
     print("Text after applying contractions: ", description)
     description = text_cleaner(description)
     print("Text after applying text_cleaner: ", description)
     tokenize_list = tokenization_func(description)
     print("Text after tokenizing: ", tokenize_list)
     # Part Of Speech Tagging
     list_of_sen_with_part_of_speech_tagging = nltk.pos_tag(tokenize_list)
     print("Text after POS: ", list_of_sen_with_part_of_speech_tagging)
     list_of_words = lemmatization(list_of_sen_with_part_of_speech_tagging)
     print("Text after lemmatization: ", list_of_words)
     
     description = str(list_of_words[0])
     
     return description

from keras.utils import pad_sequences
from keras.preprocessing.text import Tokenizer

maxlen = 100
numWords=10000

import pickle
import os

tokenizer_path = os.path.join(os.path.dirname(__file__), 'tokenizer.pickle')

# Load the tokenizer object from the saved file
with open(tokenizer_path, 'rb') as handle:
    tokenizer = pickle.load(handle)

tokenizer.char_level = False

def wordTokenizer(desc):
  tokenizer.fit_on_texts(desc) # convert each word in the text into a unique integer ID
  desc = tokenizer.texts_to_sequences(desc) # transform each text in dataframe into a sequence of integer indices
  print("tokenized desc is: ", desc)
  desc = pad_sequences(desc, maxlen = maxlen) # ensure that all sequences have the same length  
#   print("desc after pad_sequence is: ", desc)
        
  return desc

def getData(desc):
  print("Original text is: ", desc)
  X= wordTokenizer(desc) 
#   print("X is :", X)
  return X
