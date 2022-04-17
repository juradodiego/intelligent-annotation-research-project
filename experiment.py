'''
@author     Diego Jurado
@project    CS1699 / CS 1951 Term Research Project
@title      Compensating for Annotation Bias via Re-Annotation Methods
'''

# Imports
import numpy as np
import pandas as pd
from sklearn import *
from sklearn import svm
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split

''' ------ HELPER METHODS ------ '''

# Data Processing
# params: String file
# return: DataFrame df
def import_data(file):
    df = pd.read_csv(file).drop_duplicates()
    # randomly sample 3000 hate speech
    hate = df.query('Class == "hate"').sample(n=3000).copy() 
    # randomly sample 3000 non-hate speech
    non_hate = df.query('Class == "none"').sample(n=3000).copy()
    # merge hate and non-hate
    df = pd.merge(hate, non_hate, how='outer').copy()

    return df

# Data Set Information Reporting
# params: DataFrame df
def data_stat(df):
    length = len(df)
    h_length = len(df.query('Class == "hate"'))
    n_length = len(df.query('Class == "none"'))
    print("\nNumber of samples:", length,"\nNumber of Hate Samples:", h_length, "\nNumber of non-Hate Samples:", n_length)

# Randomized Re-Annotation Sampling
# params: Dataframe df, float fn, float fp
# return: DataFrame rdf
def rand_annot_samp(df, fn, fp):

    rdf = df.copy()

    fn_tweets = df.query('Class == "hate"').sample(frac=fn).Tweets.tolist()
    fp_tweets = df.query('Class == "none"').sample(frac=fp).Tweets.tolist()

    for t in fn_tweets:
        rdf.loc[df["Tweets"] == t, "Class"] = "none"
    for t in fp_tweets:
        rdf.loc[df["Tweets"] == t, "Class"] = "hate"

    print("\nTotal Amount Randomly Re-Annotated:", len(fp_tweets) + len(fn_tweets))

    return rdf

# Intelligent Re-Annotation Sampling
# params: Dataframe df, float fn, float fp
# return: DataFrame idf
def inte_annot_samp(df, tweets, fn, fp):

    W_NORM = np.linalg.norm(clf.coef_)
    dist = []
    idf = df.copy()

    for t in tweets:
        x = vectorizer.fit_transform([t])
        x = x.toarray()

        zeros = [[0] for l in range(0,5000 - len(x[0]))]
        
        x = np.append(x,zeros)
        x = np.reshape(x,(1,-1))

        dist.append((clf.decision_function(x) / W_NORM)[0])

    dict = {"Tweets" : tweets, "Distance" : dist}

    new_df = pd.DataFrame.from_dict(dict)

    final = pd.merge(df, new_df)

    final.sort_values(by="Distance", inplace=True)

    p_to_n = 0
    n_to_p = 0
    for index, row in final.iterrows():
        tweet = row["Tweets"]
        dist = row["Distance"]

        if (row["Class"] == "hate" and p_to_n != int(fn * 3000)):
            idf.loc[idf["Tweets"] == tweet, "Class"] = "none"
            p_to_n += 1

        elif (row["Class"] == "none" and n_to_p != int(fp * 3000)):
            idf.loc[idf["Tweets"] == tweet, "Class"] = "hate"
            n_to_p += 1
    
        if n_to_p == int(fp * 3000) and p_to_n == int(fn * 3000):
            break
            
    print("\nTotal Amount of Re-annotations:", int(fp * 3000) + int(fn * 3000))

    return idf

''' ------ MAIN METHOD ------ '''

results = {}

trials = 16

for trial in range(1,trials):
    print("\nTrial:", trial)
    t = []
    # ------ Baseline ------ #

    # Data Processing
    df = import_data("dataset.csv")

    # Data Set Info
    # data_stat(df)

    # Data Split
    X_train, X_test, Y_train, Y_test = train_test_split(df.Tweets, df.Class, test_size=0.2)

    vectorizer = CountVectorizer(analyzer = "word",tokenizer = None,preprocessor = None,stop_words = None,max_features = 5000)

    train_data_features = vectorizer.fit_transform(X_train)
    train_data_features = train_data_features.toarray()
    
    test_data_features = vectorizer.transform(X_test)
    test_data_features = test_data_features.toarray()

    # Classifier
    clf=svm.SVC(kernel='linear', C=1.0)

    print ("\nTraining Baseline SVM")
    clf.fit(train_data_features,Y_train)

    print ("\nTesting Baseline SVM")
    predicted=clf.predict(test_data_features)

    accuracy=np.mean(predicted==Y_test)

    # TO-DO: Format Accuracy Str
    # print ("\nBaseline Accuracy: ",accuracy) 
    t.append(accuracy)

    t_dict = {"Tweets" : X_test, "Actual" : Y_test, "Predicted" : predicted}
    df2 = pd.DataFrame(t_dict).reset_index()

    fn_tweets = df2.query('Actual == "hate" and Actual != Predicted').Tweets.copy()
    fp_tweets = df2.query('Actual == "none" and Actual != Predicted').Tweets.copy()

    fn = len(fn_tweets) / len(df2)
    fp = len(fp_tweets) / len(df2)

    tweets = fn_tweets.append(fp_tweets) 
    tweets = tweets.tolist()

    # ------ Random Sampling ------ #

    # Data Processing
    rdf = rand_annot_samp(df, fn, fp)

    # Data Set Info
    # data_stat(rdf)

    # Data Split
    X_train, X_test, Y_train, Y_test = train_test_split(rdf.Tweets, rdf.Class, test_size=0.2)

    train_data_features = vectorizer.fit_transform(X_train)
    train_data_features = train_data_features.toarray()

    test_data_features = vectorizer.transform(X_test)
    test_data_features = test_data_features.toarray()

    # Classifier
    r_clf = svm.SVC(kernel='linear', C=1.0)

    print("\nTraining Random Sampling SVM")
    r_clf.fit(train_data_features,Y_train)

    print("\nTesting Random Sampling SVM")
    r_predicted = r_clf.predict(test_data_features)

    r_accuracy=np.mean(r_predicted==Y_test)
    t.append(r_accuracy)
   
    # print ("\nRandom Accuracy: ",r_accuracy) 
   

    # ------ Intelligent Sampling ------ #

    # Data Processing
    idf = inte_annot_samp(df, tweets, fn, fp)
    
    # Data Split
    X_train, X_test, Y_train, Y_test = train_test_split(idf.Tweets, idf.Class, test_size=0.2)

    train_data_features = vectorizer.fit_transform(X_train)
    train_data_features = train_data_features.toarray()

    test_data_features = vectorizer.transform(X_test)
    test_data_features = test_data_features.toarray()

    # Classifier
    i_clf = svm.SVC(kernel='linear', C=1.0)

    print("\nTraining Intelligent Sampling SVM")
    i_clf.fit(train_data_features,Y_train)

    print("Testing Intelligent Sampling SVM")
    i_predicted = i_clf.predict(test_data_features)

    i_accuracy = np.mean(i_predicted==Y_test)
    t.append(i_accuracy)
    # TO-DO: Format Accuracy Str
    # print ("\nIntelligent Accuracy: ",i_accuracy)  
    
    # Appending results
    s = str(trial)
    results[s] = t


results = pd.DataFrame.from_dict(results)
results.to_csv("results.csv")

b_change = []
r_change = []
i_change = []
for trial in range(1,trials):
    bl = results.iloc[0][trial]
    rand = results.iloc[1][trial]
    inte = results.iloc[2][trial]

    b_change.append((bl-bl) * 100)
    r_change.append((rand-bl) * 100)
    i_change.append((inte-bl) * 100)

print("Avg Baseline Change: " + str(sum(b_change) / len(b_change)) + "%")
print("Avg Random Change: " + str(sum(r_change) / len(r_change)) + "%")
print("Avg Intelligent Change: " + str(sum(i_change) / len(i_change)) + "%")