import seaborn as sns 
import matplotlib.pyplot  as plt
import pandas as pd
import boto3, botocore
import trp
import time
#from preprocess import extractMC_v2

######################################################################
############# functions to extract with Textract######################
textract = boto3.client('textract')

def extractTextract(bucket,textractObjectName):
    
    response = textract.start_document_analysis(
        DocumentLocation={
            'S3Object': {
                'Bucket': bucket,
                'Name': textractObjectName
            }},
        FeatureTypes=[
            'TABLES',
        ]
        )

    textractJobId = response["JobId"]
    print('job id is: ',textractJobId)
    time.sleep(15)
    response = textract.get_document_analysis(JobId=textractJobId)
    status = response["JobStatus"]

    while(status == "IN_PROGRESS"):
        time.sleep(5)
        response = textract.get_document_analysis(JobId=textractJobId)
        status = response["JobStatus"]
        print("Textract Job status: {}".format(status))
    
    pages=extract_text(textractJobId,response)
    doc = trp.Document(pages)
    return doc


def extract_text(textractJobId,response):
    pages = []

    time.sleep(5)

    response = textract.get_document_analysis(JobId=textractJobId)

    pages.append(response)

    nextToken = None
    if('NextToken' in response):
        nextToken = response['NextToken']

    while(nextToken):
        time.sleep(5)

        response = textract.get_document_analysis(JobId=textractJobId, NextToken=nextToken)

        pages.append(response)
        print("Resultset page recieved: {}".format(len(pages)))
        nextToken = None
        if('NextToken' in response):
            nextToken = response['NextToken']
    
    return pages 
  

########################################################################
############# functions to extract with comprehend######################
maxLength=10000


comprehend_medical_client = boto3.client(service_name='comprehendmedical', region_name='us-east-1')


def extractMedical(doc):
    comprehendResponse = []
    for page in doc.pages:
        pageText = page.text
    
        for i in range(0, len(pageText), maxLength):
            response = comprehend_medical_client.detect_entities_v2(Text=pageText[0+i:maxLength+i])
            comprehendResponse.append(response)
        patient_string = ""
        
    #df_cm=extractMC_v2(comprehendResponse[0])
    return comprehendResponse

#############################################################################################
############# functions to convert all medical conditions to 1 record ########################
