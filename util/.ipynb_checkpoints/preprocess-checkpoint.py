import seaborn as sns 
import matplotlib.pyplot  as plt
import pandas as pd
import boto3, botocore


class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


def retrieve_mcList(df, nFeature=20,threshold=0.9):
    ## change all terms to lower case
    df['MEDICAL_CONDITION']=df['MEDICAL_CONDITION'].str.lower()
    ## 
    df=df.replace(['hemostatic','hematoma','Hemostasis'],'hemostasis')
    df=df.replace(['wounds','masses','lesions','polyps'],['wound' ,'mass','lesion','polyp'])
    mcList=df[df.Score>=threshold].MEDICAL_CONDITION.value_counts().index[:nFeature].to_list()
    
    
    return mcList, df



def mc_barplot(df, threshold_score=0.9,topN=20):
    df_mcs_vc = df.MEDICAL_CONDITION[df.Score>0.9].value_counts()

    df_mcs_top = df_mcs_vc[:topN,]
    plt.figure(figsize=(20,5))
    chart=sns.barplot(df_mcs_top.index, df_mcs_top.values, alpha=0.8)
    chart.set_xticklabels(chart.get_xticklabels(), rotation=45)
    plt.title(f'top {topN} medical conditions in the patients')
    plt.ylabel('Number of Occurrences', fontsize=12)
    plt.xlabel('occurance', fontsize=14)
    plt.show()
    return df_mcs_vc


## extract medical conditions in a batch


import pandas as pd
def extractMC_v2(json_file):
    list_icd10=[]
    medical_conditions=[]
    scores=[]
    traits=[]
    for row in json_file['Entities']:
        # 
        if row['Category'] == "MEDICAL_CONDITION":
            medical_conditions.append(row['Text'])#  += row['Text'] + ' '
            scores.append(row['Score'])
            trait='NaN'
            if row['Traits']:
                #print(row['Traits'],row['Text'] )
                trait=row['Traits'][0]['Name']
                
            traits.append(trait)
        df_mc = pd.DataFrame({'MEDICAL_CONDITION': pd.Series(medical_conditions), 'Score':pd.Series(scores),'Trait':pd.Series(traits)})
    return df_mc


def extractMCbatch(transcriptionList,patientIDList):
    df_final = pd.DataFrame()
    #patient_id=100
    #assert(len(transcriptionList)==len(patientIDList)):
    if(len(transcriptionList)!=len(patientIDList)):
        return("Error! different length!")

    
    for item,patient_id in zip(transcriptionList,patientIDList):
        
        df_ind = extractMC_v2(item)
        df_ind['ID']=patient_id
        patient_id=patient_id+1
        df_final=df_final.append(df_ind)
      
    
    # remove the duplicated entries 
    df_final=df_final.sort_values(by=['ID','MEDICAL_CONDITION']).drop_duplicates(['ID','MEDICAL_CONDITION'],keep='last')

    #print(df_final.shape)
    
    return df_final


from tqdm import tqdm
import boto3

## this function will extract the subpopulation
def subpopulation_comprehend(df, medical_specialty,sampleSize=200):
    ## select the sub population
    df_sub=df[df.medical_specialty==medical_specialty ].reset_index()
    #df_sub.head()

    ## sample from the population
    df_sub_sub=df_sub.sample(n=sampleSize, random_state=123)
    print("original data shape is ",df_sub_sub.shape)

    ## remove missing entries
    df_sub_sub=df_sub_sub[df_sub_sub.transcription.notna()==True]
    print("data shape after removing missing entries is ",df_sub_sub.shape)

    #patient_ids=df_sub_sub['id'].to_list()
   
    
    cm  = boto3.client(service_name='comprehendmedical', use_ssl=True, region_name = 'us-east-1')
    #idx=0
    #print("df_sub_sub['transcription'] ", len(df_sub_sub['transcription']))
    patient_ids=df_sub_sub['id'].to_list()
    ## comprehend processing
    # transcrption_list=df_sub_sub['id'].to_list()
    transcrption_list=[]
    for text in tqdm(df_sub_sub['transcription']):
        #print(idx)
        #print("----------------")
        #print("analyzing:", text)
        comprehend_result = cm.detect_entities_v2(Text = text)
        #print(len(comprehend_result))
        transcrption_list.append(comprehend_result)
        
        
    return transcrption_list, patient_ids


def corrPlot(df):
    plt.figure(figsize=(15,15))
    corr = df.iloc[:,1:].corr() ## skip the 1st column as it is the patient_id
    ax = sns.heatmap(
        corr, 
        vmin=-1, vmax=1, center=0,
        cmap=sns.diverging_palette(20, 220, n=200),
        square=True
        )
    ax.set_xticklabels(ax.get_xticklabels(),
        rotation=45,
        horizontalalignment='right'
        );
    
    return

##### function to interate the medical conditions and then convert to a wide formate

def dataframe_convert(df_raw,df_final, condition ):
    
    #step1: get the sub dataframe 
    df_sub = df_raw[df_raw.MEDICAL_CONDITION==condition]
    
    #step2: iterate the sub dataframe and fill the information into the native ones
    for index, row  in df_sub.iterrows():
        #print(row)
        sid=row.ID
       
        #print("condition is:",condition)
        df_final.loc[df_final.ID == sid,condition]=row.Score
        #print("Processed: ",df_final.columns)
    return df_final



#### predict for single record ##
def predict_from_numpy(predictor, data):
    # Configure predictor for CSV input:
    predictor.content_type = "text/csv"
    predictor.serializer = sagemaker.predictor.csv_serializer
    # Fetch result and load back to numpy:
    return np.fromstring(predictor.predict(data).decode("utf-8"), sep=",")

##### the function to convert dataframe of medical conditions from long format to wide format


colname_mc=['nontender', 'foreign body', 'edema', 'alert', 'murmur',
       'chest pain', 'vomiting', 'hiatal hernia', 'distress', 'hemostasis',
       'carpal tunnel syndrome', 'endometriosis', 'weakness', 'pain', 'mass',
       'inflammation', 'polyp', 'bleeding', 'hypertension', 'supple', 'fever',
       'stenosis', 'wound', 'cyanosis', 'infection', 'erythema',
       'normocephalic', 'fracture', 'lesion', 'ulceration', 'nausea', 'cough',
       'tumor', 'soft', 'shortness of breath', 'injury', 'diabetes']




def df_mc_generator(df_mcs,colname_mc=colname_mc ,colname_other=['ID',"Label"] ):
    
    ## remove duplicate rows
    df_1 = df_mcs.drop_duplicates(subset=['ID']).copy()
   
    ## generate an empty dataframe first
    column_names=colname_other+colname_mc
    ## column names
    df_combined=pd.DataFrame(columns=column_names)
    ## copy ID and positive data from the original df
    df_combined[colname_other]=df_1[colname_other]
   
    ## loop to fill in the information for each condition
    for con in colname_mc:
        #print(df_combined.columns)
        df_combined = dataframe_convert(df_mcs,df_combined, con )
    df_combined = df_combined.fillna(0)
    df_combined["Label"] = df_combined["Label"].astype(int)
    
    return df_combined

def df_mc_generator_slim(df_mcs,colname_mc=colname_mc ,colname_other=['ID'] ): 
    
    ## remove duplicate rows
    df_1 = df_mcs.drop_duplicates(subset=['ID']).copy()
    #print(colname_mc)
    ## generate an empty dataframe first
    column_names=colname_other+colname_mc
    ## column names
    df_combined=pd.DataFrame(columns=column_names)
    ## copy ID and positive data from the original df
    df_combined[colname_other]=df_1[colname_other]
   
    ## loop to fill in the information for each condition
    for con in colname_mc:
        #print(df_combined.columns)
        df_combined = dataframe_convert(df_mcs,df_combined, con )
    df_combined = df_combined.fillna(0)
    #df_combined["Label"] = df_combined["Label"].astype(int)
    
    return df_combined
