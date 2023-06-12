!pip install pdfminer
!pip install docx2txt
#install modules required for web page rendering 
!pip install pyngrok==4.1.1
!pip install flask_ngrok
#ngrok token for authentication 
!ngrok authtoken 2GGL91rTLJMxq8BHT2TAtDWzru4_6SDVjWjxx2f5aybd2JfXT 
#importing modules required for natural language processing
import io
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
#Docx resume
import docx2txt
#Wordcloud
import re
import operator
import nltk
nltk.download('stopwords')
nltk.download('punkt')
from nltk.tokenize import word_tokenize 
from nltk.corpus import stopwords
set(stopwords.words('english'))
#import modules to create wordcloud
from wordcloud import WordCloud
#import modules required to calculate score
from nltk.probability import FreqDist
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
#import modules required for plotting and sowing wordcloud
import matplotlib.pyplot as plt
#import modules required for moving files
import os
import shutil
#import flask modules to create the flask app
from flask_ngrok import run_with_ngrok
from flask import Flask, render_template,flash
from flask import request 

#mount google drive
from google.colab import drive

drive.mount('/content/gdrive')
#function to read pdf file
def read_pdf_resume(pdf_doc):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle)
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(pdf_doc, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True,check_extractable=True):           
            page_interpreter.process_page(page)     
        text = fake_file_handle.getvalue() 
    # close open handles      
    converter.close() 
    fake_file_handle.close() 
    if text:     
        return text

#function to read word doc
def read_word_resume(word_doc):
     resume = docx2txt.process(word_doc)
     resume = str(resume)
     #print(resume)
     text =  ''.join(resume)
     text = text.replace("\n", "")
     if text:
         return text

#function to clean job description
def clean_job_decsription(jd):
     ''' a function to create a word cloud based on the input text parameter'''
     ## Clean the Text
     # Lower
     clean_jd = jd.lower()
     # remove punctuation
     clean_jd = re.sub(r'[^\w\s]', '', clean_jd)
     # remove trailing spaces
     clean_jd = clean_jd.strip()
     # remove numbers
     clean_jd = re.sub('[0-9]+', '', clean_jd)
     # tokenize 
     clean_jd = word_tokenize(clean_jd)
     # remove stop words
     stop = stopwords.words('english')
     clean_jd = [w for w in clean_jd if not w in stop] 
     return(clean_jd)         

#function to create word cloud
def create_word_cloud(jd):
     corpus = jd
     fdist = FreqDist(corpus)
	#print(fdist.most_common(100))
     words = ' '.join(corpus)
     words = words.split()
     
     # create a empty dictionary  
     data = dict() 
     #  Get frequency for each words where word is the key and the count is the value  
     for word in (words):     
        word = word.lower()     
        data[word] = data.get(word, 0) + 1 
     # Sort the dictionary in reverse order to print first the most used terms
     dict(sorted(data.items(), key=operator.itemgetter(1),reverse=True)) 
     word_cloud = WordCloud(width = 800, height = 800, 
     background_color ='white',max_words = 500) 
     word_cloud.generate_from_frequencies(data) 
    
     # plot the WordCloud image
     plt.figure(figsize = (10, 8), edgecolor = 'k')
     plt.imshow(word_cloud,interpolation = 'bilinear')  
     plt.axis("off")  
     plt.tight_layout(pad = 0)
     plt.show()
     if os.path.exists("/content/gdrive/MyDrive/static/img.png"):
       os.remove("/content/gdrive/MyDrive/static/img.png")
     word_cloud.to_file('img.png')
     shutil.move("/content/img.png", "/content/gdrive/MyDrive/static")
     
     
#function to get matching score
def get_resume_score(text):
    cv = CountVectorizer(stop_words='english')
    count_matrix = cv.fit_transform(text)
    #Print the similarity scores
    print("\nSimilarity Scores:")
     
    #get the match percentage
    matchPercentage = cosine_similarity(count_matrix)[0][1] * 100
    matchPercentage = round(matchPercentage, 2) # round to two decimal
     
    result = "Your resume matches about "+ str(matchPercentage)+ "% of the job description."
    return result

#create flask app
#set the template folder where templates are stored
#set the static folder where images are stored
app = Flask(__name__,template_folder='/content/gdrive/MyDrive/templates',static_folder='/content/gdrive/MyDrive/static')
run_with_ngrok(app)
#text() function is run when the home page url is loaded
@app.route('/')
def text():
  return render_template('ResumeChecker.html')
#predict() function is called when the /predict page opens  
@app.route('/predict',methods=['POST'])  
def predict():
  #extract data from the submitted form
   filetype=request.form['filetype']
   f=request.files['file']
   f.save(f.filename)
   jobdescription=request.form['jobdescription']
   #initialise error
   error=None
   #based on filetype call a function to parse the profile
   if filetype=='none':
     error="Select a valid file type"
     return render_template('ResumeChecker.html',error=error)
   
   name,ext = os.path.splitext(f.filename)  
   ext=ext[1:]
   print(ext)
   print(filetype)
   if ext!=filetype:
     error="File type does not match with selected type"
     return render_template('ResumeChecker.html',error=error)

   if filetype=='pdf':
     resume=read_pdf_resume(f.filename)
   else :
     resume=read_word_resume(f.filename)

    #clean job description and extract words
   clean_jd = clean_job_decsription(jobdescription) 
   #call function to create wordcloud 
   create_word_cloud(clean_jd)
   
   #get result as matching percentage
   text = [resume, jobdescription] 
   result = get_resume_score(text)
   #render the results page
   return render_template('predict.html',result=result) 
@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
 